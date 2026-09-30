"""Phase 1a: build data/work/panel.parquet from the card-month source.

Adds derived columns only (market_total, lidl_share, n_chains). Does not
re-clean the source spend columns.
"""
import duckdb

from common import load_config, path


def main():
    cfg = load_config()
    chains = cfg["chains"]
    cols = [chains["spend_columns"][c] for c in chains["all"]]
    lidl_col = chains["spend_columns"][chains["hero"]]

    src = path(cfg["data"]["card_month_path"])
    out = path("data/work/panel.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW src AS SELECT * FROM read_csv_auto('{src}')")

    market_total = " + ".join(cols)
    n_chains_expr = " + ".join(f"CASE WHEN {c} > 0 THEN 1 ELSE 0 END" for c in cols)

    con.execute(f"""
        COPY (
            SELECT
                card, month, pstl_cd_enr, flag_lidl, crd_typ_nm, avg_txn_value,
                {', '.join(cols)},
                ({market_total})::DOUBLE AS market_total,
                CASE WHEN ({market_total}) > 0 THEN {lidl_col} / ({market_total}) ELSE NULL END AS lidl_share,
                ({n_chains_expr}) AS n_chains
            FROM src
        ) TO '{out}' (FORMAT PARQUET)
    """)

    n = con.sql(f"SELECT COUNT(*) AS n FROM read_parquet('{out}')").df().n[0]
    print(f"Wrote {out} ({n} rows)")


if __name__ == "__main__":
    main()
