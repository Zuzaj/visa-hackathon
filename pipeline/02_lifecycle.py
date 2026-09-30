"""Phase 1b: apply the lifecycle_rules to the panel and build
data/work/lifecycle.parquet, data/work/wins.parquet, and a funnel summary.

With only 2 months of history, `is_regular` cannot clear its 4-month trailing
window for any card, so lifecycle/funnel output is expected to be empty (or
near-empty) right now. Nothing here is hardcoded to 2 months: pointing
`config.yaml`'s data path at the full 18-month file and re-running is enough
to get real output, with no code changes.
"""
import duckdb
import pandas as pd

from common import load_config, path
from lifecycle_rules import (
    classify_destination,
    classify_stayer,
    find_lapse,
    find_wins,
    is_regular,
    month_add,
    month_range,
)


def build_card_series(df: pd.DataFrame, chains: dict) -> dict:
    """card -> {
        'lidl_positive': {month: bool}, 'area': {month: str},
        'chain_spend': {chain: {month: float}}, 'market_total': {month: float},
    }"""
    lidl_col = chains["spend_columns"][chains["hero"]]
    chain_cols = {c: chains["spend_columns"][c] for c in chains["all"]}
    out = {}
    for card, g in df.groupby("card"):
        g = g.set_index("month")
        out[card] = {
            "lidl_positive": (g[lidl_col] > 0).to_dict(),
            "area": g["pstl_cd_enr"].to_dict(),
            "chain_spend": {c: g[col].to_dict() for c, col in chain_cols.items()},
            "market_total": g["market_total"].to_dict(),
        }
    return out


def window_sum(series: dict, months: list[int]) -> float:
    return sum(series.get(m, 0.0) for m in months)


def area_unchanged(area_by_month: dict, months: list[int]) -> bool:
    seen = {area_by_month[m] for m in months if area_by_month.get(m) is not None}
    return len(seen) <= 1


def main():
    cfg = load_config()
    chains = cfg["chains"]
    lc = cfg["lifecycle"]
    hero = chains["hero"]

    panel_path = path("data/work/panel.parquet")
    con = duckdb.connect()
    df = con.sql(f"SELECT * FROM read_parquet('{panel_path}')").df()

    first_month, last_month = int(df.month.min()), int(df.month.max())
    all_months = month_range(first_month, last_month)
    print(f"Panel covers {first_month}..{last_month} ({len(all_months)} months)")

    series = build_card_series(df, chains)

    lifecycle_rows = []
    wins_rows = []
    regular_by_card_month = {}  # (card, month) -> bool/None, for the funnel

    for card, s in series.items():
        lidl_positive = s["lidl_positive"]
        regular_at = {
            m: is_regular(lidl_positive, m, first_month, lc["regular_window_months"], lc["regular_min_months"])
            for m in all_months
        }
        for m in all_months:
            regular_by_card_month[(card, m)] = regular_at[m]

        regular_true = {m: v for m, v in regular_at.items() if v is True}
        if not regular_true:
            continue

        lapse_month = find_lapse(regular_true, lidl_positive, last_month,
                                  lc["lapse_window_months"], lc["edge_exclusion_months"])
        if lapse_month is None:
            continue

        before = month_range(month_add(lapse_month, -lc["destination_window_months"]), month_add(lapse_month, -1))
        after = month_range(lapse_month, month_add(lapse_month, lc["destination_window_months"] - 1))

        other_chains = [c for c in chains["all"] if c != hero]
        spend_before = window_sum(s["market_total"], before)
        other_spend_after = sum(window_sum(s["chain_spend"][c], after) for c in other_chains)
        active_months_after = sum(
            1 for m in after if sum(s["chain_spend"][c].get(m, 0.0) for c in other_chains) > 0
        )
        unchanged = area_unchanged(s["area"], before + after)

        status = classify_stayer(active_months_after, unchanged, lc["stayer_min_active_months"])
        bucket = destination = None
        if status == "stayer":
            bucket = classify_destination(spend_before, other_spend_after, lc["switch_threshold_share"])
            gains = {c: window_sum(s["chain_spend"][c], after) for c in other_chains}
            destination = max(gains, key=gains.get) if gains else None

        lifecycle_rows.append({
            "card": card, "regular_from": min(regular_true), "lapsed_month": lapse_month,
            "status": status, "bucket": bucket, "destination_chain": destination,
        })

        card_wins = find_wins(lidl_positive, {c: s["chain_spend"][c] for c in other_chains},
                               all_months, lc["win_min_absence_months"])
        for win_month, source_chain in card_wins:
            wins_rows.append({"card": card, "win_month": win_month, "source_chain": source_chain})

    lifecycle = pd.DataFrame(lifecycle_rows, columns=["card", "regular_from", "lapsed_month", "status", "bucket", "destination_chain"])
    wins = pd.DataFrame(wins_rows, columns=["card", "win_month", "source_chain"])

    out_lifecycle = path("data/work/lifecycle.parquet")
    out_wins = path("data/work/wins.parquet")
    lifecycle.to_parquet(out_lifecycle, index=False)
    wins.to_parquet(out_wins, index=False)
    print(f"Wrote {out_lifecycle} ({len(lifecycle)} rows), {out_wins} ({len(wins)} rows)")

    # Funnel summary
    print("\n=== Funnel ===")
    funnel = []
    for m in all_months:
        active_regulars = sum(1 for (c, mm), v in regular_by_card_month.items() if mm == m and v is True)
        lapsed_stayers = sum(1 for r in lifecycle_rows if r["lapsed_month"] == m and r["status"] == "stayer")
        vanished_or_moved = sum(1 for r in lifecycle_rows if r["lapsed_month"] == m and r["status"] in ("vanished", "mover"))
        funnel.append({"month": m, "active_regulars": active_regulars,
                        "lapsed_stayers": lapsed_stayers, "vanished_or_moved": vanished_or_moved})
    funnel_df = pd.DataFrame(funnel)
    print(funnel_df.to_string(index=False))
    funnel_df.to_parquet(path("data/work/funnel.parquet"), index=False)

    insufficient = sum(1 for v in regular_by_card_month.values() if v is None)
    print(f"\ncard-months with insufficient_history for the regular rule: {insufficient} / {len(regular_by_card_month)}")


if __name__ == "__main__":
    main()
