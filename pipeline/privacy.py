"""Privacy rules shared by every export in data/out/ (plan section 5/12):
k-anonymity (k_min distinct cards per row) and no card-level identifiers.
"""
import pandas as pd


def enforce_k_min(df: pd.DataFrame, k_min: int, n_cards_col: str = "n_cards") -> pd.DataFrame:
    """Drop any row backed by fewer than k_min distinct cards."""
    if df.empty:
        return df
    return df[df[n_cards_col] >= k_min].reset_index(drop=True)


def suppress_small_counts(df: pd.DataFrame, count_cols: list, k_min: int) -> pd.DataFrame:
    """Null out any count that is positive but below k_min (a true zero is not
    a k-anonymity risk and is left as-is)."""
    df = df.copy()
    for col in count_cols:
        mask = (df[col] > 0) & (df[col] < k_min)
        df.loc[mask, col] = None
    return df


def assert_exportable(df: pd.DataFrame, name: str) -> None:
    """Raise if a dataframe about to be written to data/out/ carries a card id
    or any column literally named 'card'."""
    forbidden = {"card", "pymt_crd_acct_num_raw", "card_id"}
    hit = forbidden & set(df.columns)
    if hit:
        raise ValueError(f"{name}: exported aggregate must not contain card ids, found {hit}")
