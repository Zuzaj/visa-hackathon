"""Phase 0 (raw source -> card-month CSV): builds data/raw/card_month_4month.csv
from the raw Visa parquet drop (data/raw/datasprint_sample_data.parquet).

Reproducible replacement for the exploratory dask notebook at
pipeline/notebooks/extract_card_month_data.ipynb -- same merchant-name ->
chain mapping and card x month aggregation logic, but in DuckDB so a full
scan of the ~17GB / 305M-row parquet (pushdown-filtered to Poznan grocery
transactions first) takes seconds instead of minutes, and needs no dask
dependency. Run with: python pipeline/extract_card_month_csv.py

Merchant filter: mrch_catg_cd = 5411 (grocery stores/supermarkets),
mrch_ctry_cd = 616 (Poland), merchant city = Poznan. This is the STORE's
city, not the cardholder's -- the app's "whole sample is Poznan cardholders"
assumption is really "Poznan grocery-store transactions", a close but not
identical proxy (catches a small amount of visitor/commuter spend, misses
Poznan residents shopping at a store just outside city limits).
"""
import duckdb

from common import load_config, path

# Raw merchant-name prefix (lowercased) each tracked chain is identified by.
# Must have exactly one entry per chain in config.yaml's chains.all -- see
# the assertion in main(). Chosen by inspecting distinct merchant names per
# prefix against the raw data (pipeline/notebooks/extract_card_month_data.ipynb).
MERCHANT_PREFIXES = {
    "lidl": "lidl",
    "kaufland": "kaufland",
    "biedronka": "jmp",  # Biedronka trades under its owner, Jeronimo Martins Polska
    "netto": "netto",
    "stokrotka": "stokrotka",
    "aldi": "aldi",
    "carrefour": "carrefour",
    "auchan": "auchan",
    "intermarche": "intermarche",
    "spolem": "wss",  # local Spolem-network co-op stores trade as "WSS Detal"
    "dino": "dino",
}

MCC_GROCERY = 5411
COUNTRY_POLAND = 616
MERCHANT_CITY = "poznan"


def main():
    cfg = load_config()
    chains = cfg["chains"]
    chain_names = chains["all"]

    missing = [c for c in chain_names if c not in MERCHANT_PREFIXES]
    if missing:
        raise SystemExit(f"No merchant-name prefix mapped for chains {missing} -- add them to MERCHANT_PREFIXES.")

    src = path("data/raw/datasprint_sample_data.parquet")
    out = path(cfg["data"]["card_month_path"])
    out.parent.mkdir(parents=True, exist_ok=True)

    start_month, end_month = 202501, 202504  # the 4-month window this app currently serves

    con = duckdb.connect()
    con.execute("PRAGMA threads=8")

    con.execute(f"""
        CREATE VIEW filtered AS
        SELECT
            pymt_crd_acct_num_raw AS card,
            prch_mnth_id AS month,
            pstl_cd_enr,
            crd_typ_nm,
            cs_tran_amt::DOUBLE AS cs_tran_amt,
            lower(mrch_nm_raw) AS mrch_lower
        FROM read_parquet('{src}')
        WHERE mrch_catg_cd = {MCC_GROCERY}
          AND mrch_ctry_cd = {COUNTRY_POLAND}
          AND lower(mrch_city_nm_raw) = '{MERCHANT_CITY}'
          AND prch_mnth_id BETWEEN {start_month} AND {end_month}
    """)

    spd_cols = [chains["spend_columns"][name] for name in chain_names]
    spd_exprs = [
        f"CASE WHEN mrch_lower LIKE '{MERCHANT_PREFIXES[name]}%' THEN cs_tran_amt ELSE 0 END AS {chains['spend_columns'][name]}"
        for name in chain_names
    ]
    lidl_cond = f"mrch_lower LIKE '{MERCHANT_PREFIXES[chains['hero']]}%'"
    other_cond = " OR ".join(
        f"mrch_lower LIKE '{MERCHANT_PREFIXES[name]}%'" for name in chain_names if name != chains["hero"]
    )
    tracked_cond = " OR ".join(f"mrch_lower LIKE '{p}%'" for p in MERCHANT_PREFIXES.values())

    con.execute(f"""
        CREATE VIEW rows AS
        SELECT
            card, month, pstl_cd_enr, crd_typ_nm,
            {', '.join(spd_exprs)},
            CASE WHEN {lidl_cond} THEN 1 ELSE 0 END AS is_lidl,
            CASE WHEN {other_cond} THEN 1 ELSE 0 END AS is_other,
            CASE WHEN ({tracked_cond}) THEN 1 ELSE 0 END AS is_tracked
        FROM filtered
    """)

    tracked_spend_sum = " + ".join(f"sum({c})" for c in spd_cols)

    con.execute(f"""
        COPY (
            SELECT
                card, month,
                max(pstl_cd_enr) AS pstl_cd_enr,
                max(crd_typ_nm) AS crd_typ_nm,
                {', '.join(f'sum({c}) AS {c}' for c in spd_cols)},
                CASE
                    WHEN max(is_lidl) = 1 AND max(is_other) = 1 THEN 'lidl_and_other'
                    WHEN max(is_lidl) = 1 THEN 'lidl_only'
                    WHEN max(is_other) = 1 THEN 'other_only'
                    ELSE 'none'
                END AS flag_lidl,
                CASE WHEN sum(is_tracked) > 0 THEN ({tracked_spend_sum}) / sum(is_tracked) ELSE NULL END AS avg_txn_value
            FROM rows
            GROUP BY card, month
        ) TO '{out}' (HEADER, DELIMITER ',')
    """)

    n = con.sql(f"SELECT COUNT(*) AS n FROM read_csv_auto('{out}')").df().n[0]
    print(f"Wrote {out} ({n} card-month rows, chains: {', '.join(chain_names)})")


if __name__ == "__main__":
    main()
