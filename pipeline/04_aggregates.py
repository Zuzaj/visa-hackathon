"""Phase 2: cross-sectional aggregates that need no lifecycle history --
computable from however many months are in the panel today (2, eventually
18). Writes wallet_share, cross_shopping, overlap, poznan_signal, and a copy
of the funnel into data/out/, all k-anonymized and card-id-free.

The whole sample is Poznan data -- see aggregates_lib.py's module docstring.
"""
import pandas as pd

from aggregates_lib import (
    build_cross_shopping,
    build_customer_profile,
    build_overlap,
    build_switch_rate,
    build_switch_signal,
    build_wallet_share,
)
from common import load_config, path
from privacy import assert_exportable, enforce_k_min, suppress_small_counts


def main():
    cfg = load_config()
    chains_cfg = cfg["chains"]
    k_min = cfg["privacy"]["k_min"]
    recent_window = cfg["lifecycle"]["recent_window_months"]

    panel = pd.read_parquet(path("data/work/panel.parquet"))
    out_dir = path("data/out")
    out_dir.mkdir(parents=True, exist_ok=True)

    wallet_share = enforce_k_min(build_wallet_share(panel, chains_cfg, k_min), k_min)
    cross_shopping = enforce_k_min(build_cross_shopping(panel, chains_cfg, recent_window), k_min, "n_cards_segment")
    overlap = enforce_k_min(build_overlap(panel, chains_cfg, recent_window), k_min)
    switch_signal = enforce_k_min(build_switch_signal(panel, chains_cfg, k_min), k_min)
    switch_rate = enforce_k_min(build_switch_rate(panel, chains_cfg, k_min), k_min, "n_switched")

    customer_segments, customer_profile, tier_cutoffs = build_customer_profile(
        panel, chains_cfg, k_min,
        regular_window=cfg["lifecycle"]["regular_window_months"],
        regular_min=cfg["lifecycle"]["regular_min_months"],
    )
    customer_segments = enforce_k_min(customer_segments, k_min)
    customer_profile = enforce_k_min(customer_profile, k_min)
    spend_tiers = pd.DataFrame([tier_cutoffs]) if tier_cutoffs else pd.DataFrame(columns=["low_max", "medium_max"])

    for name, df in [
        ("wallet_share", wallet_share), ("cross_shopping", cross_shopping),
        ("overlap", overlap), ("poznan_signal", switch_signal),
        ("switch_rate", switch_rate), ("customer_segments", customer_segments),
        ("customer_profile", customer_profile), ("spend_tiers", spend_tiers),
    ]:
        assert_exportable(df, name)
        df.to_parquet(out_dir / f"{name}.parquet", index=False)
        print(f"{name}: {len(df)} rows")

    funnel_src = path("data/work/funnel.parquet")
    if funnel_src.exists():
        funnel = pd.read_parquet(funnel_src)
        count_cols = ["active_regulars", "lapsed_stayers", "vanished_or_moved"]
        funnel = suppress_small_counts(funnel, count_cols, k_min)
        assert_exportable(funnel, "funnel")
        funnel.to_parquet(out_dir / "funnel.parquet", index=False)
        print(f"funnel: {len(funnel)} rows")


if __name__ == "__main__":
    main()
