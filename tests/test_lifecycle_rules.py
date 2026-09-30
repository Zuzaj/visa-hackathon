from lifecycle_rules import (
    classify_destination,
    classify_stayer,
    find_lapse,
    find_wins,
    is_regular,
    month_add,
    month_range,
)


def to_positive(months_with_spend: list[int]) -> dict[int, bool]:
    return {m: True for m in months_with_spend}


# --- month arithmetic -------------------------------------------------

def test_month_add_within_year():
    assert month_add(202503, 2) == 202505
    assert month_add(202503, -2) == 202501


def test_month_add_across_year_boundary():
    assert month_add(202511, 3) == 202602
    assert month_add(202601, -1) == 202512


def test_month_range_inclusive():
    assert month_range(202511, 202602) == [202511, 202512, 202601, 202602]


# --- is_regular ---------------------------------------------------------

def test_is_regular_needs_full_trailing_window():
    # window=4, but only 2 months of history exist -> insufficient_history
    lidl_positive = to_positive([202501, 202502])
    assert is_regular(lidl_positive, 202502, first_month=202501, window=4, min_months=3) is None


def test_is_regular_true_with_enough_months():
    # 3 of the trailing 4 months have Lidl spend -> regular
    lidl_positive = to_positive([202501, 202502, 202504])
    result = is_regular(lidl_positive, 202504, first_month=202501, window=4, min_months=3)
    assert result is True


def test_is_regular_false_with_too_few_months():
    lidl_positive = to_positive([202501])
    result = is_regular(lidl_positive, 202504, first_month=202501, window=4, min_months=3)
    assert result is False


# --- find_lapse -----------------------------------------------------------

def test_find_lapse_detects_two_zero_months_after_regular():
    regular_at = {202504: True, 202505: True}
    lidl_positive = to_positive([202501, 202502, 202503, 202504])  # zero from 202505 on
    lapse = find_lapse(regular_at, lidl_positive, last_month=202508,
                        lapse_window=2, edge_exclusion=2)
    assert lapse == 202505


def test_find_lapse_none_when_card_keeps_buying():
    regular_at = {202504: True}
    lidl_positive = to_positive([202501, 202502, 202503, 202504, 202505, 202506])
    lapse = find_lapse(regular_at, lidl_positive, last_month=202508,
                        lapse_window=2, edge_exclusion=2)
    assert lapse is None


def test_find_lapse_respects_edge_exclusion():
    # Lapse would start at 202508, but last_confirmable = 202508 - 2 = 202506,
    # and the lapse window [202508, 202509] extends past it -> not confirmable yet.
    regular_at = {202507: True}
    lidl_positive = to_positive([202501, 202502, 202503, 202504, 202505, 202506, 202507])
    lapse = find_lapse(regular_at, lidl_positive, last_month=202509,
                        lapse_window=2, edge_exclusion=2)
    assert lapse is None


# --- classify_destination -------------------------------------------------

def test_classify_destination_switched():
    # recovers 70%+ of prior spend elsewhere
    assert classify_destination(spend_before=100, other_spend_after=80,
                                 switch_threshold_share=0.7) == "switched"


def test_classify_destination_spending_less():
    assert classify_destination(spend_before=100, other_spend_after=40,
                                 switch_threshold_share=0.7) == "spending_less"


def test_classify_destination_vanished_or_moved():
    assert classify_destination(spend_before=100, other_spend_after=0,
                                 switch_threshold_share=0.7) == "vanished_or_moved"


def test_classify_destination_buckets_sum_to_100_pct_of_stayers():
    # any positive other_spend_after must land in exactly one of switched/spending_less
    cases = [(100, 1), (100, 69.99), (100, 70), (100, 500)]
    for before, after in cases:
        result = classify_destination(before, after, 0.7)
        assert result in ("switched", "spending_less")


# --- classify_stayer --------------------------------------------------

def test_classify_stayer_mover_takes_priority():
    assert classify_stayer(active_months_after=3, area_unchanged=False,
                            stayer_min_active_months=2) == "mover"


def test_classify_stayer_stayer():
    assert classify_stayer(active_months_after=2, area_unchanged=True,
                            stayer_min_active_months=2) == "stayer"


def test_classify_stayer_vanished():
    assert classify_stayer(active_months_after=0, area_unchanged=True,
                            stayer_min_active_months=2) == "vanished"


# --- find_wins --------------------------------------------------------

def test_find_wins_attributes_to_chain_with_largest_drop():
    months = [202501, 202502, 202503, 202504]
    lidl_positive = {202501: False, 202502: False, 202503: False, 202504: True}
    competitor_spend = {
        "biedronka": {202503: 100.0, 202504: 20.0},   # big drop
        "kaufland": {202503: 50.0, 202504: 45.0},     # small drop
    }
    wins = find_wins(lidl_positive, competitor_spend, months, win_min_absence_months=2)
    assert wins == [(202504, "biedronka")]


def test_find_wins_requires_absence_window():
    # Lidl-positive the whole time -> never counts as a "win"
    months = [202501, 202502, 202503]
    lidl_positive = {202501: True, 202502: True, 202503: True}
    competitor_spend = {"biedronka": {202502: 100.0, 202503: 10.0}}
    wins = find_wins(lidl_positive, competitor_spend, months, win_min_absence_months=2)
    assert wins == []


def test_find_wins_no_win_without_competitor_drop():
    months = [202501, 202502, 202503]
    lidl_positive = {202501: False, 202502: False, 202503: True}
    competitor_spend = {"biedronka": {202502: 10.0, 202503: 20.0}}  # rose, not dropped
    wins = find_wins(lidl_positive, competitor_spend, months, win_min_absence_months=2)
    assert wins == []
