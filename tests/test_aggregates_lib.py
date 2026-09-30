import pandas as pd

from aggregates_lib import (
    build_customer_profile,
    build_overlap,
    build_switch_rate,
    build_switch_signal,
    build_wallet_share,
    classify_lidl_segment,
    segment_for,
)

CHAINS_CFG = {
    "hero": "lidl",
    "all": ["lidl", "kaufland", "biedronka"],
    "spend_columns": {"lidl": "spd_lidl", "kaufland": "spd_kaufland", "biedronka": "spd_biedronka"},
    "pooled_groups": {"other_discounters": ["biedronka"], "other_formats": ["kaufland"]},
}


def make_panel(rows):
    """rows: list of (card, month, lidl, kaufland, biedronka)"""
    return pd.DataFrame(rows, columns=["card", "month", "spd_lidl", "spd_kaufland", "spd_biedronka"])


# --- segment_for -----------------------------------------------------

def test_segment_for_lidl_only():
    assert segment_for({"lidl"}, "lidl") == "lidl_only"


def test_segment_for_none():
    assert segment_for(set(), "lidl") == "none"


def test_segment_for_other_only():
    assert segment_for({"biedronka"}, "lidl") == "other_only"


def test_segment_for_lidl_plus_2():
    assert segment_for({"lidl", "kaufland", "biedronka"}, "lidl") == "lidl_plus_2_or_more"


# --- build_wallet_share: total_spend/n_customers suppression -------------

def test_wallet_share_suppresses_absolutes_below_k_min_but_keeps_share():
    rows = []
    # 25 cards shop lidl; only 5 shop kaufland -- kaufland's absolutes must be
    # suppressed (below k_min=20) but its share should still be reported.
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))
    for i in range(25, 30):
        rows.append((f"c{i}", 202501, 0, 50, 0))
    panel = make_panel(rows)
    panel["market_total"] = panel[["spd_lidl", "spd_kaufland", "spd_biedronka"]].sum(axis=1)
    result = build_wallet_share(panel, CHAINS_CFG, k_min=20)

    lidl_row = result[result.chain == "lidl"].iloc[0]
    assert lidl_row.n_customers == 25
    assert lidl_row.total_spend == 2500
    assert lidl_row.share is not None

    kaufland_row = result[result.chain == "kaufland"].iloc[0]
    assert pd.isna(kaufland_row.n_customers)
    assert pd.isna(kaufland_row.total_spend)
    assert not pd.isna(kaufland_row.share)  # ratio stays even when absolutes are suppressed


def test_wallet_share_keeps_absolutes_at_or_above_k_min():
    rows = [(f"c{i}", 202501, 100, 0, 0) for i in range(20)]
    panel = make_panel(rows)
    panel["market_total"] = panel[["spd_lidl", "spd_kaufland", "spd_biedronka"]].sum(axis=1)
    result = build_wallet_share(panel, CHAINS_CFG, k_min=20)
    lidl_row = result[result.chain == "lidl"].iloc[0]
    assert lidl_row.n_customers == 20
    assert lidl_row.total_spend == 2000


# --- build_switch_signal: this is the privacy-sensitive one --------------

def test_switch_signal_below_k_min_is_suppressed_entirely():
    # Only 5 cards decline -- below k_min=20, so nothing should be reported,
    # not even a rounded/approximate count.
    rows = []
    for i in range(5):
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 50, 60, 0))  # lidl fell, kaufland rose
    panel = make_panel(rows)
    result = build_switch_signal(panel, CHAINS_CFG, k_min=20)
    assert result.empty


def test_switch_signal_attributes_destination_by_group_not_chain():
    # 25 cards: lidl spend falls from 100 to 40; kaufland (other_formats) rises
    # more than biedronka (other_discounters). Destination must be the GROUP
    # name, never the individual competitor's name.
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 40, 50, 10))
    panel = make_panel(rows)
    result = build_switch_signal(panel, CHAINS_CFG, k_min=20)
    assert len(result) == 1
    row = result.iloc[0]
    assert row.destination == "other_formats"
    assert row.destination not in ("kaufland", "biedronka")  # never a competitor's real name
    assert row.n_cards == 25
    assert row.n_cards_declining_total == 25
    assert row.share == 1.0


def test_switch_signal_sums_gains_across_group_members():
    # Two chains share the "wide_group": individually each gains less than
    # "narrow_group"'s single chain, but their COMBINED gain is larger --
    # destination must reflect the group total, not any single chain.
    cfg = {
        "hero": "lidl",
        "all": ["lidl", "a", "b", "c"],
        "spend_columns": {"lidl": "spd_lidl", "a": "spd_a", "b": "spd_b", "c": "spd_c"},
        "pooled_groups": {"wide_group": ["a", "b"], "narrow_group": ["c"]},
    }
    rows = []
    for i in range(25):
        rows.append({"card": f"c{i}", "month": 202501, "spd_lidl": 100, "spd_a": 0, "spd_b": 0, "spd_c": 0})
        # a gains 30, b gains 30 (wide_group total 60); c gains 40 (narrow_group total 40)
        rows.append({"card": f"c{i}", "month": 202502, "spd_lidl": 40, "spd_a": 30, "spd_b": 30, "spd_c": 40})
    panel = pd.DataFrame(rows)
    result = build_switch_signal(panel, cfg, k_min=20)
    assert len(result) == 1
    assert result.iloc[0].destination == "wide_group"


def test_switch_signal_ignores_cards_whose_lidl_spend_did_not_fall():
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 100, 50, 0))  # lidl unchanged, not "declining"
    panel = make_panel(rows)
    result = build_switch_signal(panel, CHAINS_CFG, k_min=20)
    assert result.empty


def test_switch_signal_covers_every_consecutive_month_pair():
    # Two separate declining events: 202501->202502 (destination: kaufland/
    # other_formats) and 202502->202503 (destination: biedronka/other_discounters).
    # Both must appear, tagged by their own month_to, so the UI can select either.
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 40, 50, 0))
        rows.append((f"c{i}", 202503, 10, 50, 40))
    panel = make_panel(rows)
    result = build_switch_signal(panel, CHAINS_CFG, k_min=20)
    assert set(result.month_to) == {202502, 202503}
    first = result[result.month_to == 202502].iloc[0]
    assert first.destination == "other_formats"
    second = result[result.month_to == 202503].iloc[0]
    assert second.destination == "other_discounters"


# --- build_overlap: must report groups, never individual competitors -----

def test_overlap_never_exposes_individual_chain_names():
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 50, 0))  # lidl + kaufland (other_formats)
    panel = make_panel(rows)
    result = build_overlap(panel, CHAINS_CFG, recent_window=3)
    reported_names = set(result.group_a) | set(result.group_b)
    assert reported_names.issubset({"lidl", "other_discounters", "other_formats"})
    assert "kaufland" not in reported_names
    assert "biedronka" not in reported_names


def test_overlap_computes_group_level_share():
    rows = []
    # 25 lidl+kaufland shoppers, 10 of whom also shop biedronka
    for i in range(25):
        biedronka = 20 if i < 10 else 0
        rows.append((f"c{i}", 202501, 100, 50, biedronka))
    panel = make_panel(rows)
    result = build_overlap(panel, CHAINS_CFG, recent_window=3)
    row = result[(result.group_a == "other_formats") & (result.group_b == "other_discounters")].iloc[0]
    assert row.n_cards == 25
    assert row.share_of_shoppers == 10 / 25


def test_overlap_has_one_snapshot_per_month():
    # Month 1: everyone shops kaufland only. Month 2: everyone adds biedronka.
    # Selecting either month must recompute the overlap for that month alone.
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 50, 0))
        rows.append((f"c{i}", 202502, 100, 50, 20))
    panel = make_panel(rows)
    result = build_overlap(panel, CHAINS_CFG, recent_window=1)  # window=1 -> no history bleed
    assert set(result.month) == {202501, 202502}
    m1_row = result[(result.month == 202501) & (result.group_a == "other_formats") & (result.group_b == "other_discounters")].iloc[0]
    assert m1_row.share_of_shoppers == 0
    m2_row = result[(result.month == 202502) & (result.group_a == "other_formats") & (result.group_b == "other_discounters")].iloc[0]
    assert m2_row.share_of_shoppers == 1.0


# --- build_switch_rate: "was a Lidl customer, now isn't" -----------------

def test_switch_rate_counts_only_prior_lidl_customers_who_left():
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))  # lidl customer in month 1
        rows.append((f"c{i}", 202502, 0, 0, 0))    # gone in month 2 -> switched
    for i in range(25, 50):
        rows.append((f"c{i}", 202501, 0, 50, 0))   # never a lidl customer
        rows.append((f"c{i}", 202502, 0, 50, 0))
    panel = make_panel(rows)
    result = build_switch_rate(panel, CHAINS_CFG, k_min=20)
    assert len(result) == 1
    row = result.iloc[0]
    assert row.lidl_customers_prior == 25
    assert row.n_switched == 25
    assert row.switch_rate == 1.0


def test_switch_rate_excludes_customers_who_stayed_or_reduced_but_not_to_zero():
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 40, 0, 0))  # still > 0 -> not "switched"
    panel = make_panel(rows)
    result = build_switch_rate(panel, CHAINS_CFG, k_min=20)
    assert result.empty  # n_switched = 0, nothing to report


def test_switch_rate_suppressed_when_switchers_below_k_min():
    rows = []
    for i in range(25):
        stay_zero = i < 5  # only 5 actually drop to zero
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 0 if stay_zero else 40, 0, 0))
    panel = make_panel(rows)
    result = build_switch_rate(panel, CHAINS_CFG, k_min=20)
    assert result.empty  # 5 switchers < k_min=20


def test_switch_rate_covers_every_consecutive_month_pair():
    rows = []
    for i in range(25):
        rows.append((f"c{i}", 202501, 100, 0, 0))
        rows.append((f"c{i}", 202502, 0, 0, 0))    # everyone switches by month 2
        rows.append((f"c{i}", 202503, 0, 50, 0))   # already gone, no new switch
    panel = make_panel(rows)
    result = build_switch_rate(panel, CHAINS_CFG, k_min=20)
    assert set(result.month_to) == {202502}  # 202502->202503 has 0 prior lidl customers


# --- classify_lidl_segment -----------------------------------------------

MONTHS = [202501, 202502, 202503, 202504]


def test_classify_never_a_lidl_customer():
    assert classify_lidl_segment({m: 0 for m in MONTHS}, MONTHS) is None


def test_classify_gone_was_active_now_zero():
    spend = {202501: 100, 202502: 80, 202503: 50, 202504: 0}
    assert classify_lidl_segment(spend, MONTHS) == "gone"


def test_classify_gone_missing_row_counts_as_zero():
    spend = {202501: 100, 202502: 80, 202503: 50}  # no entry for 202504 at all
    assert classify_lidl_segment(spend, MONTHS) == "gone"


def test_classify_not_gone_if_only_a_single_trial_month():
    # One month of Lidl spend, ever -- never reached "regular", so this is
    # excluded entirely rather than counted as a churned customer.
    spend = {202501: 100, 202502: 0, 202503: 0, 202504: 0}
    assert classify_lidl_segment(spend, MONTHS) is None


def test_classify_not_gone_if_never_reached_regular_threshold():
    # Two active months out of four -- below regular_min=3, so still excluded.
    spend = {202501: 100, 202502: 80, 202503: 0, 202504: 0}
    assert classify_lidl_segment(spend, MONTHS) is None


def test_classify_gone_respects_custom_regular_threshold():
    # With a looser bar (regular_min=2), the same two-active-month card DOES
    # count as having been "regular" before leaving.
    spend = {202501: 100, 202502: 80, 202503: 0, 202504: 0}
    assert classify_lidl_segment(spend, MONTHS, regular_window=4, regular_min=2) == "gone"


def test_classify_loyal_active_every_month_no_decline():
    spend = {202501: 50, 202502: 60, 202503: 55, 202504: 70}
    assert classify_lidl_segment(spend, MONTHS) == "loyal"


def test_classify_fading_takes_priority_over_loyal():
    # Active every month (would otherwise be "loyal"), but strictly declining.
    spend = {202501: 100, 202502: 80, 202503: 60, 202504: 40}
    assert classify_lidl_segment(spend, MONTHS) == "fading"


def test_classify_fading_allows_plateaus_but_needs_net_decrease():
    spend = {202501: 100, 202502: 100, 202503: 50, 202504: 50}
    assert classify_lidl_segment(spend, MONTHS) == "fading"


def test_classify_not_fading_if_trend_reverses():
    # Dips then recovers -- net change is still down, but not monotonic, so
    # this should NOT be flagged as a consistent decline.
    spend = {202501: 50, 202502: 100, 202503: 80, 202504: 40}
    assert classify_lidl_segment(spend, MONTHS) != "fading"


def test_classify_drifting_irregular_no_decline():
    spend = {202501: 0, 202502: 50, 202503: 0, 202504: 60}
    assert classify_lidl_segment(spend, MONTHS) == "drifting"


def test_classify_drifting_single_recent_month():
    spend = {202501: 0, 202502: 0, 202503: 0, 202504: 40}
    assert classify_lidl_segment(spend, MONTHS) == "drifting"


# --- build_customer_profile ------------------------------------------------

PROFILE_CHAINS_CFG = {
    "hero": "lidl",
    "all": ["lidl", "kaufland"],
    "spend_columns": {"lidl": "spd_lidl", "kaufland": "spd_kaufland"},
}


def make_profile_panel(cards_spec):
    """cards_spec: list of (card, monthly_lidl_spend[4], card_type, avg_txn_value)"""
    rows = []
    for card, spend, card_type, txn in cards_spec:
        for month, s in zip(MONTHS, spend):
            rows.append({
                "card": card, "month": month, "spd_lidl": s, "spd_kaufland": 0,
                "crd_typ_nm": card_type, "avg_txn_value": txn,
            })
    return pd.DataFrame(rows)


def test_customer_profile_segments_and_a_rare_card_type_is_suppressible():
    # build_customer_profile itself returns raw counts (like build_switch_signal) --
    # 04_aggregates.py applies enforce_k_min on top of both summary and profile,
    # using their own n_cards column. This test checks the raw counts are right
    # and that the rare row would indeed fail a k_min=20 check downstream.
    cards = []
    for i in range(25):
        cards.append((f"loyal{i}", [50, 50, 50, 50], "CLASSIC", 40))
    for i in range(25):
        cards.append((f"gone{i}", [50, 50, 50, 0], "CLASSIC", 40))  # regular (3/4), then left
    cards.append(("rare1", [50, 50, 50, 50], "PLATINUM", 40))
    panel = make_profile_panel(cards)

    summary, profile, _ = build_customer_profile(panel, PROFILE_CHAINS_CFG, k_min=20)

    assert set(summary.segment) == {"loyal", "gone"}
    loyal_n = summary.loc[summary.segment == "loyal", "n_cards"].iloc[0]
    assert loyal_n == 26  # 25 CLASSIC + 1 PLATINUM

    loyal_card_types = profile[(profile.segment == "loyal") & (profile.dimension == "card_type")]
    platinum_row = loyal_card_types[loyal_card_types.value == "PLATINUM"]
    assert len(platinum_row) == 1
    assert platinum_row.n_cards.iloc[0] < 20  # would be dropped by enforce_k_min(..., k_min=20)


def test_customer_profile_spend_tiers_from_population_terciles():
    cards = []
    for i in range(20):
        cards.append((f"low{i}", [50, 50, 50, 50], "CLASSIC", 10))
    for i in range(20):
        cards.append((f"mid{i}", [50, 50, 50, 50], "CLASSIC", 50))
    for i in range(20):
        cards.append((f"high{i}", [50, 50, 50, 50], "CLASSIC", 200))
    panel = make_profile_panel(cards)

    summary, profile, cutoffs = build_customer_profile(panel, PROFILE_CHAINS_CFG, k_min=20)

    assert "low_max" in cutoffs and "medium_max" in cutoffs
    tiers = profile[(profile.segment == "loyal") & (profile.dimension == "spend_tier")]
    tier_counts = dict(zip(tiers.value, tiers.n_cards))
    assert tier_counts.get("low") == 20
    assert tier_counts.get("medium") == 20
    assert tier_counts.get("high") == 20
