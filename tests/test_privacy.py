import pandas as pd
import pytest

from privacy import assert_exportable, enforce_k_min, suppress_small_counts


def test_enforce_k_min_drops_rows_below_threshold():
    df = pd.DataFrame({"n_cards": [5, 19, 20, 100], "value": [1, 2, 3, 4]})
    result = enforce_k_min(df, k_min=20)
    assert result.n_cards.min() >= 20
    assert len(result) == 2


def test_enforce_k_min_keeps_empty_frame_empty():
    df = pd.DataFrame({"n_cards": [], "value": []})
    result = enforce_k_min(df, k_min=20)
    assert result.empty


def test_suppress_small_counts_nulls_positive_below_k_but_keeps_zero():
    df = pd.DataFrame({"count": [0, 5, 19, 20]})
    result = suppress_small_counts(df, ["count"], k_min=20)
    assert result["count"].tolist()[0] == 0        # true zero untouched
    assert pd.isna(result["count"].iloc[1])         # 5 suppressed
    assert pd.isna(result["count"].iloc[2])         # 19 suppressed
    assert result["count"].iloc[3] == 20             # 20 kept


def test_assert_exportable_rejects_card_id_column():
    df = pd.DataFrame({"card": ["abc"], "n_cards": [50]})
    with pytest.raises(ValueError):
        assert_exportable(df, "some_table")


def test_assert_exportable_allows_clean_aggregate():
    df = pd.DataFrame({"month": [202501], "n_cards": [50]})
    assert_exportable(df, "some_table")  # should not raise


def test_every_exported_parquet_respects_k_min_and_has_no_card_id():
    """Integration check for Phase 2's acceptance criteria: run against
    whatever the pipeline has actually written to data/out/."""
    import pathlib

    out_dir = pathlib.Path(__file__).resolve().parents[1] / "data" / "out"
    files = sorted(out_dir.glob("*.parquet"))
    if not files:
        pytest.skip("no exported aggregates yet -- run the pipeline first")

    k_min = 20
    for f in files:
        df = pd.read_parquet(f)
        assert "card" not in df.columns, f"{f.name} contains a card id column"
        for col in df.columns:
            if col == "n_cards" or col.startswith("n_cards"):
                positive = df[col].dropna()
                positive = positive[positive > 0]
                assert (positive >= k_min).all(), f"{f.name}.{col} has a positive count below k_min"
