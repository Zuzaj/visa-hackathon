"""Phase 0: inspect the card-month data. Prints results only -- no cleaning,
no writes. Run with: python pipeline/00_inspect.py
"""
import pathlib

import duckdb
import pandas as pd
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
pd.set_option("display.width", 200)


def load_config():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def connect(cfg):
    path = ROOT / cfg["data"]["card_month_path"]
    con = duckdb.connect()
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_csv_auto('{path}')")
    return con


def check_flag_lidl(con, chains):
    other_sum = " + ".join(chains["spend_columns"][c] for c in chains["all"] if c != chains["hero"])
    lidl_col = chains["spend_columns"][chains["hero"]]
    print("\n=== 1. flag_lidl distinct values + crosstab vs spend ===")
    print(con.sql("SELECT flag_lidl, COUNT(*) AS n FROM t GROUP BY 1 ORDER BY n DESC").df())
    print(con.sql(f"""
        SELECT flag_lidl,
               SUM(CASE WHEN {lidl_col} > 0 THEN 1 ELSE 0 END) AS lidl_pos,
               SUM(CASE WHEN {other_sum} > 0 THEN 1 ELSE 0 END) AS other_pos,
               COUNT(*) AS n
        FROM t GROUP BY 1 ORDER BY n DESC
    """).df())


def check_counts(con):
    print("\n=== 2. Row / card / month counts ===")
    print(con.sql("""
        SELECT COUNT(*) AS n_rows, COUNT(DISTINCT card) AS n_cards,
               COUNT(DISTINCT month) AS n_months, MIN(month) AS min_month, MAX(month) AS max_month
        FROM t
    """).df())
    print(con.sql("SELECT month, COUNT(*) AS n FROM t GROUP BY 1 ORDER BY 1").df())
    print("Cards by number of active months:")
    print(con.sql("""
        SELECT months_active, COUNT(*) AS n_cards FROM (
            SELECT card, COUNT(*) AS months_active FROM t GROUP BY 1
        ) GROUP BY 1 ORDER BY 1
    """).df())


def check_zero_and_outliers(con, chains):
    cols = [chains["spend_columns"][c] for c in chains["all"]]
    zero_expr = " AND ".join(f"{c} = 0" for c in cols)
    neg_expr = " OR ".join(f"{c} < 0" for c in cols)
    print("\n=== 3. All-zero rows, negative values, spend distribution ===")
    print(con.sql(f"""
        SELECT
            SUM(CASE WHEN {zero_expr} THEN 1 ELSE 0 END) AS all_zero_rows,
            SUM(CASE WHEN {neg_expr} THEN 1 ELSE 0 END) AS negative_rows,
            COUNT(*) AS total
        FROM t
    """).df())
    print(con.sql(f"SUMMARIZE SELECT {', '.join(cols)} FROM t").df())


def check_geography(con, cfg):
    geo_col = cfg["geography"]["level"]
    k_min = cfg["privacy"]["k_min"]
    print(f"\n=== 4. Geography ({geo_col}): nulls, distinct values, cell sizes ===")
    print(con.sql(f"""
        SELECT SUM(CASE WHEN {geo_col} IS NULL THEN 1 ELSE 0 END) AS nulls,
               COUNT(*) AS total, COUNT(DISTINCT {geo_col}) AS distinct_values
        FROM t
    """).df())
    dist = con.sql(f"""
        SELECT cards_in_area, COUNT(*) AS n_areas FROM (
            SELECT {geo_col}, COUNT(DISTINCT card) AS cards_in_area
            FROM t WHERE {geo_col} IS NOT NULL GROUP BY 1
        ) GROUP BY 1 ORDER BY 1
    """).df()
    print(dist.to_string())
    meets_k = dist.loc[dist.cards_in_area >= k_min, "n_areas"].sum()
    total_areas = dist.n_areas.sum()
    print(f"Areas meeting k_min={k_min}: {meets_k} / {total_areas}")


def check_movers(con, cfg):
    geo_col = cfg["geography"]["level"]
    print(f"\n=== 5. Movers: cards whose {geo_col} changes across the available months ===")
    print(con.sql(f"""
        SELECT SUM(CASE WHEN n_areas > 1 THEN 1 ELSE 0 END) AS movers, COUNT(*) AS total_cards
        FROM (
            SELECT card, COUNT(DISTINCT {geo_col}) AS n_areas
            FROM t WHERE {geo_col} IS NOT NULL GROUP BY 1
        )
    """).df())


def check_vanish_rate(con, cfg, chains):
    """Among Lidl regulars, share with zero spend at all six chains in the
    3 months after a given month. Needs regular_window_months + 3 months of
    history -- not computable yet with only 2 months in the sample."""
    n_months = con.sql("SELECT COUNT(DISTINCT month) AS n FROM t").df().n[0]
    needed = cfg["lifecycle"]["regular_window_months"] + 3
    print(f"\n=== 6. Vanish rate ===")
    if n_months < needed:
        print(f"SKIPPED: needs >= {needed} months of history, sample has {n_months}. "
              f"Re-run once the full data lands.")
        return
    # Left as future work once enough months exist.


def main():
    cfg = load_config()
    con = connect(cfg)
    chains = cfg["chains"]

    check_flag_lidl(con, chains)
    check_counts(con)
    check_zero_and_outliers(con, chains)
    check_geography(con, cfg)
    check_movers(con, cfg)
    check_vanish_rate(con, cfg, chains)


if __name__ == "__main__":
    main()
