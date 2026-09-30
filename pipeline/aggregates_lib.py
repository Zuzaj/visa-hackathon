"""Pure aggregate-building logic used by 04_aggregates.py, split out (like
lifecycle_rules.py) so it can be unit-tested directly against small
DataFrames without needing the real panel or file I/O.

The whole card-month sample is Poznan cardholders (per the data provider),
so there is no national-vs-regional split here -- every aggregate below
describes Poznan. `geography.active_city` in config.yaml is the label to
show for it; see api/main.py for how the "other cities" placeholder list
is served for the home screen.
"""
import itertools

import pandas as pd

from lifecycle_rules import is_regular, month_add, month_range


def chain_group(chain: str, chains_cfg: dict) -> str:
    if chain == chains_cfg["hero"]:
        return "lidl"
    for group, members in chains_cfg["pooled_groups"].items():
        if group == "hero_label":
            continue
        if chain in members:
            return group
    return chain


def build_wallet_share(panel: pd.DataFrame, chains_cfg: dict, k_min: int) -> pd.DataFrame:
    """Per (month, chain): market share, plus the absolute total spend (VC)
    and customer count. The two absolute columns are nulled out if the chain
    has fewer than k_min customers that month -- `share` stays populated
    either way, since a ratio doesn't reveal a small group's size the way a
    raw headcount or total would.
    """
    cols = chains_cfg["spend_columns"]
    rows = []
    for month, g in panel.groupby("month"):
        cohort = g[g.market_total > 0]
        n_cards = cohort.card.nunique()
        total = cohort.market_total.sum()
        if total <= 0:
            continue
        for chain in chains_cfg["all"]:
            spend = cohort[cols[chain]]
            total_spend = float(spend.sum())
            n_customers = int((spend > 0).sum())
            suppressed = n_customers < k_min
            rows.append({
                "month": month, "chain": chain, "chain_group": chain_group(chain, chains_cfg),
                "share": total_spend / total, "n_cards": n_cards,
                "total_spend": None if suppressed else total_spend,
                "n_customers": None if suppressed else n_customers,
            })
    return pd.DataFrame(rows)


def chains_used_by_card(panel: pd.DataFrame, chains_cfg: dict, window_months: list) -> dict:
    cols = chains_cfg["spend_columns"]
    sub = panel[panel.month.isin(window_months)]
    used: dict = {}
    for chain, col in cols.items():
        for card in sub.loc[sub[col] > 0, "card"].unique():
            used.setdefault(card, set()).add(chain)
    return used


def segment_for(chains_used: set, hero: str) -> str:
    if not chains_used:
        return "none"
    others = chains_used - {hero}
    if hero not in chains_used:
        return "other_only"
    if not others:
        return "lidl_only"
    if len(others) == 1:
        return "lidl_plus_1"
    return "lidl_plus_2_or_more"


def build_cross_shopping(panel: pd.DataFrame, chains_cfg: dict, recent_window: int) -> pd.DataFrame:
    first_month, last_month = int(panel.month.min()), int(panel.month.max())
    all_months = month_range(first_month, last_month)
    rows = []
    for month in all_months:
        window_start = max(first_month, month_add(month, -(recent_window - 1)))
        window = month_range(window_start, month)
        used = chains_used_by_card(panel, chains_cfg, window)
        # include cards with a row in `month` but zero chain usage in the window
        cards_this_month = set(panel.loc[panel.month == month, "card"])
        segments = [segment_for(used.get(c, set()), chains_cfg["hero"]) for c in cards_this_month]
        n_cards = len(cards_this_month)
        counts = pd.Series(segments).value_counts()
        for seg, n in counts.items():
            rows.append({"month": month, "segment": seg, "n_cards_segment": int(n),
                         "share": n / n_cards, "n_cards": n_cards})
    return pd.DataFrame(rows)


def build_overlap(panel: pd.DataFrame, chains_cfg: dict, recent_window: int) -> pd.DataFrame:
    """Overlap between {lidl, <pooled groups>} shopper sets, one snapshot per
    month (each using its own trailing `recent_window`) so the UI can recompute
    it for whichever month is selected -- deliberately at group granularity,
    never individual chains, since competitor identities must not be shown
    (see chain_group()).
    """
    first_month, last_month = int(panel.month.min()), int(panel.month.max())
    all_months = month_range(first_month, last_month)
    all_groups = sorted({chain_group(c, chains_cfg) for c in chains_cfg["all"]})

    rows = []
    for month in all_months:
        window_start = max(first_month, month_add(month, -(recent_window - 1)))
        window = month_range(window_start, month)
        used = chains_used_by_card(panel, chains_cfg, window)

        by_group: dict = {g: set() for g in all_groups}
        for card, chains in used.items():
            for c in chains:
                by_group[chain_group(c, chains_cfg)].add(card)

        for a, b in itertools.permutations(all_groups, 2):
            shoppers_a = by_group[a]
            if not shoppers_a:
                continue
            both = shoppers_a & by_group[b]
            rows.append({
                "month": month, "group_a": a, "group_b": b,
                "share_of_shoppers": len(both) / len(shoppers_a),
                "n_cards": len(shoppers_a),
            })
    return pd.DataFrame(rows)


SWITCH_SIGNAL_COLUMNS = ["month_from", "month_to", "n_cards_declining_total", "destination", "n_cards", "share"]


def _switch_signal_for_pair(panel: pd.DataFrame, chains_cfg: dict, k_min: int, m1: int, m2: int) -> list:
    hero_col = chains_cfg["spend_columns"][chains_cfg["hero"]]
    other_chains = [c for c in chains_cfg["all"] if c != chains_cfg["hero"]]

    p1 = panel[panel.month == m1].set_index("card")
    p2 = panel[panel.month == m2].set_index("card")
    common = p1.index.intersection(p2.index)
    p1, p2 = p1.loc[common], p2.loc[common]

    declining = common[(p1[hero_col] > 0) & (p2[hero_col] < p1[hero_col])]
    total_declining = len(declining)
    if total_declining < k_min:
        return []  # group itself too small to report, even before a destination split

    chain_deltas = {
        c: p2.loc[declining, chains_cfg["spend_columns"][c]] - p1.loc[declining, chains_cfg["spend_columns"][c]]
        for c in other_chains
    }
    groups = sorted({chain_group(c, chains_cfg) for c in other_chains})
    group_deltas = pd.DataFrame({
        g: sum(chain_deltas[c] for c in other_chains if chain_group(c, chains_cfg) == g)
        for g in groups
    }, index=declining)

    best_gain = group_deltas.max(axis=1)
    destination = group_deltas.idxmax(axis=1)[best_gain > 0]

    counts = destination.value_counts()
    return [
        {"month_from": m1, "month_to": m2, "n_cards_declining_total": total_declining,
         "destination": grp, "n_cards": int(n), "share": n / total_declining}
        for grp, n in counts.items()
    ]


SWITCH_RATE_COLUMNS = ["month_from", "month_to", "lidl_customers_prior", "n_switched", "switch_rate"]


def build_switch_rate(panel: pd.DataFrame, chains_cfg: dict, k_min: int) -> pd.DataFrame:
    """Switch rate: of cards that were Lidl customers (spd_lidl > 0) in the
    prior month, the share that are NOT Lidl customers (spd_lidl == 0) in the
    current month. One row per consecutive month pair. Independent of
    build_switch_signal -- this doesn't require identifying where the spend
    went, just whether the card left Lidl entirely.
    """
    empty = pd.DataFrame(columns=SWITCH_RATE_COLUMNS)
    hero_col = chains_cfg["spend_columns"][chains_cfg["hero"]]
    months = sorted(panel.month.unique())
    if len(months) < 2:
        return empty

    rows = []
    for m1, m2 in zip(months, months[1:]):
        p1 = panel[panel.month == m1].set_index("card")[hero_col]
        p2 = panel[panel.month == m2].set_index("card")[hero_col]
        common = p1.index.intersection(p2.index)
        p1c, p2c = p1.loc[common], p2.loc[common]

        lidl_prior = p1c > 0
        lidl_customers_prior = int(lidl_prior.sum())
        n_switched = int((lidl_prior & (p2c == 0)).sum())

        # Suppress if either the base population or the switching group itself
        # is too small to report safely -- a tiny numerator is a re-identification
        # risk even when the (already-published) denominator is large.
        if lidl_customers_prior < k_min or n_switched < k_min:
            continue

        rows.append({
            "month_from": m1, "month_to": m2,
            "lidl_customers_prior": lidl_customers_prior,
            "n_switched": n_switched,
            "switch_rate": n_switched / lidl_customers_prior,
        })
    return pd.DataFrame(rows, columns=SWITCH_RATE_COLUMNS)


def build_switch_signal(panel: pd.DataFrame, chains_cfg: dict, k_min: int) -> pd.DataFrame:
    """A 2-month proxy for 'where did Lidl's spend go' -- NOT the plan's full
    lifecycle/destination logic (that needs the 4-month regular window and
    3-month destination window; see 02_lifecycle.py). One row set per
    consecutive month pair (tagged by month_to) so the UI can recompute it
    for whichever month is selected: cards whose Lidl spend fell month over
    month, broken down by which competitor GROUP (never an individual chain)
    picked up the most of that spend.
    """
    empty = pd.DataFrame(columns=SWITCH_SIGNAL_COLUMNS)
    months = sorted(panel.month.unique())
    if len(months) < 2:
        return empty

    rows = []
    for m1, m2 in zip(months, months[1:]):
        rows.extend(_switch_signal_for_pair(panel, chains_cfg, k_min, m1, m2))
    return pd.DataFrame(rows, columns=SWITCH_SIGNAL_COLUMNS)


def classify_lidl_segment(
    lidl_spend: dict, months: list, regular_window: int = 4, regular_min: int = 3,
) -> str | None:
    """Classify a card's relationship with Lidl across `months` (a card-month
    with no row, or spend of 0, both count as "not a Lidl customer" that
    month -- same assumption used throughout this module):

    - None: never a Lidl customer in any of `months`, OR was active but never
      reached "regular" status (see is_regular, the plan's own bar: active in
      at least `regular_min` of the trailing `regular_window` months) before
      going quiet -- a single trial month shouldn't read as churn, so it's
      excluded from the segmentation entirely rather than inflating 'gone'.
    - 'gone': WAS a regular at some point, but has no Lidl spend this month.
    - 'fading': still a Lidl customer in the last month, but spend across the
      months they were active is trending down (non-increasing, with a net
      decrease) -- checked BEFORE 'loyal', since a shrinking trend is the more
      actionable signal even for a customer who is technically active every month.
    - 'loyal': a Lidl customer in every one of `months`, with no declining trend.
    - 'drifting': active in the last month but with gaps in between, and no
      clear declining trend (catch-all, including a customer only 1 month old).
    """
    positive_months = [m for m in months if lidl_spend.get(m, 0) > 0]
    if not positive_months:
        return None

    last_month = months[-1]
    first_month = months[0]
    if lidl_spend.get(last_month, 0) <= 0:
        lidl_positive = {m: lidl_spend.get(m, 0) > 0 for m in months}
        was_ever_regular = any(
            is_regular(lidl_positive, m, first_month, regular_window, regular_min) for m in months
        )
        return "gone" if was_ever_regular else None

    values = [lidl_spend[m] for m in positive_months]
    declining = (
        len(values) >= 2
        and values[0] > values[-1]
        and all(values[i] >= values[i + 1] for i in range(len(values) - 1))
    )
    if declining:
        return "fading"
    if len(positive_months) == len(months):
        return "loyal"
    return "drifting"


SEGMENT_SUMMARY_COLUMNS = ["month", "segment", "n_cards", "share"]
SEGMENT_PROFILE_COLUMNS = ["segment", "dimension", "value", "n_cards", "share"]


def build_customer_profile(
    panel: pd.DataFrame, chains_cfg: dict, k_min: int, regular_window: int = 4, regular_min: int = 3,
):
    """Segment every card that reached "regular" status with Lidl at some
    point (loyal / fading / drifting / gone, see classify_lidl_segment -- a
    one-off trial purchase is excluded, not counted as 'gone'), then profile
    each segment by card type (crd_typ_nm) and spend tier (avg_txn_value
    tercile, computed from the population actually being segmented -- not an
    arbitrary cutoff). A card's card type / spend tier is taken from its most
    recent panel row (whether or not that row has Lidl spend), so a departed
    customer's last known profile still counts. `regular_window`/`regular_min`
    should match config.yaml's lifecycle settings. Returns
    (summary_df, profile_df, tier_cutoffs).
    """
    hero_col = chains_cfg["spend_columns"][chains_cfg["hero"]]
    months = sorted(panel.month.unique())
    last_month = months[-1]

    representative = panel.loc[panel.groupby("card")["month"].idxmax()].set_index("card")
    lidl_by_card = panel.pivot_table(index="card", columns="month", values=hero_col, fill_value=0.0)

    segment_by_card = {}
    for card, row in lidl_by_card.iterrows():
        seg = classify_lidl_segment(row.to_dict(), months, regular_window, regular_min)
        if seg:
            segment_by_card[card] = seg

    empty_summary = pd.DataFrame(columns=SEGMENT_SUMMARY_COLUMNS)
    empty_profile = pd.DataFrame(columns=SEGMENT_PROFILE_COLUMNS)
    if not segment_by_card:
        return empty_summary, empty_profile, {}

    segments = pd.Series(segment_by_card, name="segment")
    total = len(segments)

    summary = pd.DataFrame([
        {"month": last_month, "segment": seg, "n_cards": int(n), "share": n / total}
        for seg, n in segments.value_counts().items()
    ], columns=SEGMENT_SUMMARY_COLUMNS)

    tx_values = representative.loc[representative.index.intersection(segments.index), "avg_txn_value"].dropna()
    tier_cutoffs = {}
    tier_by_card = pd.Series(dtype=object)
    if len(tx_values) >= 3:
        low_max, med_max = tx_values.quantile([1 / 3, 2 / 3])
        tier_cutoffs = {"low_max": float(low_max), "medium_max": float(med_max)}

        def tier_for(v):
            if pd.isna(v):
                return None
            if v <= low_max:
                return "low"
            if v <= med_max:
                return "medium"
            return "high"

        tier_by_card = representative["avg_txn_value"].apply(tier_for)

    profile_rows = []
    for seg in segments.unique():
        cards_in_seg = segments[segments == seg].index
        rep = representative.loc[representative.index.intersection(cards_in_seg)]
        seg_n = len(cards_in_seg)

        for val, n in rep["crd_typ_nm"].value_counts().items():
            profile_rows.append({"segment": seg, "dimension": "card_type", "value": val, "n_cards": int(n), "share": n / seg_n})

        if not tier_by_card.empty:
            seg_tiers = tier_by_card.loc[tier_by_card.index.intersection(cards_in_seg)].dropna()
            for val, n in seg_tiers.value_counts().items():
                profile_rows.append({"segment": seg, "dimension": "spend_tier", "value": val, "n_cards": int(n), "share": n / seg_n})

    profile = pd.DataFrame(profile_rows, columns=SEGMENT_PROFILE_COLUMNS)
    return summary, profile, tier_cutoffs
