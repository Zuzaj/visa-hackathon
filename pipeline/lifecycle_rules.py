"""Pure lifecycle logic (plan section 5). No I/O and no pandas here, so these
are trivial to unit-test against small synthetic cases (see
tests/test_lifecycle_rules.py) independent of how much real history exists.

Months are plain YYYYMM ints throughout.
"""
from __future__ import annotations


def month_add(month: int, delta: int) -> int:
    """Add `delta` calendar months to a YYYYMM int (delta may be negative)."""
    y, m = divmod(month, 100)
    idx = y * 12 + (m - 1) + delta
    y2, m2 = divmod(idx, 12)
    return y2 * 100 + (m2 + 1)


def month_range(start: int, end: int) -> list[int]:
    """Inclusive list of YYYYMM ints from start to end."""
    out, cur = [], start
    while cur <= end:
        out.append(cur)
        cur = month_add(cur, 1)
    return out


def is_regular(lidl_positive: dict[int, bool], month: int, first_month: int,
                window: int, min_months: int) -> bool | None:
    """True/False using the trailing `window` months ending at `month`.
    Returns None ("insufficient_history") if that window reaches before
    `first_month`, the first month present in the dataset. A month with no
    row for the card is treated as zero Lidl spend (not positive).
    """
    trail_start = month_add(month, -(window - 1))
    if trail_start < first_month:
        return None
    trail = month_range(trail_start, month)
    n_positive = sum(1 for m in trail if lidl_positive.get(m, False))
    return n_positive >= min_months


def find_lapse(regular_at: dict[int, bool | None], lidl_positive: dict[int, bool],
                last_month: int, lapse_window: int, edge_exclusion: int) -> int | None:
    """First month M+1 such that the card was regular at some month M and has
    zero Lidl spend in each of the next `lapse_window` months. Returns the
    lapse month, or None if the card never lapses within the confirmable
    range (the last `edge_exclusion` months of data are never confirmable).
    """
    last_confirmable = month_add(last_month, -edge_exclusion)
    for m in sorted(regular_at):
        if regular_at.get(m) is not True:
            continue
        window = month_range(month_add(m, 1), month_add(m, lapse_window))
        if window[-1] > last_confirmable:
            continue  # too close to the data edge to confirm yet
        if all(not lidl_positive.get(w, False) for w in window):
            return window[0]
    return None


def classify_destination(spend_before: float, other_spend_after: float,
                          switch_threshold_share: float) -> str:
    """'switched' | 'spending_less' | 'vanished_or_moved' for a lapsed regular.

    spend_before: total six-chain spend in the window before the lapse.
    other_spend_after: non-Lidl spend in the window after the lapse.
    """
    if other_spend_after <= 0:
        return "vanished_or_moved"
    if spend_before > 0 and other_spend_after >= switch_threshold_share * spend_before:
        return "switched"
    return "spending_less"


def classify_stayer(active_months_after: int, area_unchanged: bool,
                     stayer_min_active_months: int) -> str:
    """'stayer' if the card keeps buying groceries somewhere (non-Lidl spend
    in >= stayer_min_active_months of the destination window) and its home
    area is unchanged; 'mover' if the area changed; else 'vanished'.
    """
    if not area_unchanged:
        return "mover"
    if active_months_after >= stayer_min_active_months:
        return "stayer"
    return "vanished"


def find_wins(lidl_positive: dict[int, bool], competitor_spend: dict[str, dict[int, float]],
              months: list[int], win_min_absence_months: int) -> list[tuple[int, str]]:
    """Months where the card starts spending at Lidl after >= win_min_absence_months
    of zero Lidl spend, while a competitor's spend fell month-over-month.
    `months` must be sorted ascending. Returns (win_month, source_chain) pairs.
    """
    wins = []
    for i, m in enumerate(months):
        if not lidl_positive.get(m, False):
            continue
        if i < win_min_absence_months:
            continue
        absence = months[i - win_min_absence_months:i]
        if any(lidl_positive.get(a, False) for a in absence):
            continue
        prev = months[i - 1]
        drops = {
            chain: series.get(prev, 0.0) - series.get(m, 0.0)
            for chain, series in competitor_spend.items()
        }
        if not drops:
            continue
        best_chain = max(drops, key=drops.get)
        if drops[best_chain] > 0:
            wins.append((m, best_chain))
    return wins
