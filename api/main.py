"""Wallet Radar API. Reads only the exported aggregates in data/out/ --
never the card-month panel or anything card-level. See pipeline/ for how
those aggregates are built.

The whole card-month sample is Poznan data (confirmed by the data provider),
so there's a single set of aggregates -- no national-vs-regional split.
`geography.active_city` / `planned_cities` in config.yaml back the home
screen's area picker (one live city, others shown as "coming soon" to signal
the product is meant to scale Lidl-wide).

Hard privacy rule: individual competitor names must never leave this API.
Every response is built from the POOLED (chain_group) view -- there is no
`display_mode` override here, even though the aggregate files still carry
the underlying chain for the pipeline's own use.
"""
import pathlib
import sys

import pandas as pd
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

with open(ROOT / "config.yaml") as f:
    CONFIG = yaml.safe_load(f)

app = FastAPI(title="Wallet Radar API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def read_out(name: str) -> pd.DataFrame:
    p = ROOT / "data" / "out" / f"{name}.parquet"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_parquet(p)


def records(df: pd.DataFrame) -> list:
    """to_dict(orient='records'), but with NaN (from a suppressed cell) turned
    into a real JSON null -- bare NaN is not valid JSON and breaks the
    browser's fetch().json() the moment k-anonymity suppression ever fires.
    """
    if df.empty:
        return []
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


def pooled_wallet_share() -> pd.DataFrame:
    """wallet_share.parquet grouped to {lidl, discounts, supermarket} -- the
    only granularity ever exposed by this API."""
    df = read_out("wallet_share")
    if df.empty:
        return df
    return (
        df.groupby(["month", "chain_group"], as_index=False)
        .agg(
            share=("share", "sum"),
            n_cards=("n_cards", "first"),
            # min_count=1 so an all-suppressed group stays null instead of a misleading 0
            total_spend=("total_spend", lambda s: s.sum(min_count=1)),
            n_customers=("n_customers", lambda s: s.sum(min_count=1)),
        )
        .rename(columns={"chain_group": "series"})
    )


@app.get("/api/meta")
def meta():
    coverage = read_out("wallet_share")
    months = sorted(coverage.month.unique().tolist()) if not coverage.empty else []
    hero = CONFIG["chains"]["hero"]
    groups = [hero] + sorted(CONFIG["chains"]["pooled_groups"].keys())
    group_counts = {hero: 1, **{g: len(members) for g, members in CONFIG["chains"]["pooled_groups"].items()}}
    # Static group composition + each group's share of Poznan's TRUE grocery
    # market (see config.yaml's group_info) -- never a per-chain metric.
    group_info = CONFIG["chains"]["group_info"]
    return {
        "groups": groups,
        "group_counts": group_counts,
        "group_info": group_info,
        "lidl_market_share_pct": CONFIG["chains"]["lidl_market_share_pct"],
        "total_market_coverage_pct": CONFIG["chains"]["total_market_coverage_pct"],
        "hero": hero,
        "currency": CONFIG["currency"]["label"],
        "k_min": CONFIG["privacy"]["k_min"],
        "months_covered": months,
        "active_city": CONFIG["geography"]["active_city"],
        "planned_cities": CONFIG["geography"]["planned_cities"],
        "assumptions": [
            f"This proof of concept covers {CONFIG['geography']['active_city']} only; the product is designed to scale to any Lidl market.",
            "Cards vanishing from all tracked chains are assumed to have moved away or closed the card, and are excluded from churn.",
        ],
    }


@app.get("/api/wallet_share")
def wallet_share():
    return records(pooled_wallet_share())


@app.get("/api/cross_shopping")
def cross_shopping():
    return records(read_out("cross_shopping"))


@app.get("/api/overlap")
def overlap(month: int = None):
    df = read_out("overlap")
    if df.empty:
        return []
    target = month if month is not None else int(df.month.max())
    return records(df[df.month == target])


@app.get("/api/funnel")
def funnel():
    return records(read_out("funnel"))


@app.get("/api/overview")
def overview():
    ws = pooled_wallet_share()
    cs = read_out("cross_shopping")
    fn = read_out("funnel")

    kpis = {}
    if not ws.empty:
        months = sorted(ws.month.unique())
        latest, prior = months[-1], (months[-2] if len(months) > 1 else None)
        hero = CONFIG["chains"]["hero"]
        latest_hero = ws[(ws.month == latest) & (ws.series == hero)].share.iloc[0]
        kpis["lidl_share_latest"] = round(float(latest_hero), 4)
        kpis["latest_month"] = int(latest)
        if prior is not None:
            prior_hero = ws[(ws.month == prior) & (ws.series == hero)].share.iloc[0]
            kpis["lidl_share_change"] = round(float(latest_hero - prior_hero), 4)

    # Share of THIS month's active grocery shoppers who made no Lidl purchases
    # this month -- single-month, not the 3-month cross-shopping window (`cs`
    # is kept only because the funnel/cross_shopping files are still generated).
    if not ws.empty:
        latest_hero_row = ws[(ws.month == ws.month.max()) & (ws.series == CONFIG["chains"]["hero"])]
        if not latest_hero_row.empty and pd.notnull(latest_hero_row.n_customers.iloc[0]):
            row = latest_hero_row.iloc[0]
            kpis["no_lidl_share"] = round(1 - row.n_customers / row.n_cards, 4)

    # Active regulars can exist (needs 4 months) well before any lapse is
    # confirmable (needs 4 + lapse_window + edge_exclusion months) -- gate on
    # an actual confirmed lapse, not just on regulars existing, so the
    # switch-rate/early-warning disclaimer stays honest.
    lifecycle_ready = bool(
        not fn.empty and (fn.lapsed_stayers.fillna(0).sum() + fn.vanished_or_moved.fillna(0).sum()) > 0
    )

    return {
        "kpis": kpis,
        "lifecycle_ready": lifecycle_ready,
        "wallet_share": records(ws),
        "cross_shopping": records(cs),
    }


@app.get("/api/poznan")
def poznan(month: int = None):
    """The 'wanted poster' story: the 2-month switch-signal (see
    aggregates_lib.build_switch_signal) for the pair ending at `month` (default
    the latest available), already grouped to discounts/supermarket. Wallet
    share / KPIs are the same numbers as /api/overview -- there's no separate
    regional cut anymore.
    """
    all_signal = read_out("poznan_signal")
    target = month if month is not None else (int(all_signal.month_to.max()) if not all_signal.empty else None)
    signal = all_signal[all_signal.month_to == target] if target is not None else all_signal

    top_destination = None
    if not signal.empty:
        # Pick the leading destination from IDENTIFIED groups only -- the
        # "no clear destination" bucket added below can be the single largest
        # slice (spend can shrink with no group showing a net gain) and must
        # never be picked as if it were a competitor.
        top_row = signal.sort_values("n_cards", ascending=False).iloc[0]
        top_destination = {
            "group": top_row.destination,
            "n_cards": int(top_row.n_cards),
            "share_of_decliners": round(float(top_row.share), 4),
            "n_cards_declining_total": int(top_row.n_cards_declining_total),
            "month_from": int(top_row.month_from),
            "month_to": int(top_row.month_to),
        }

        # The two destination groups only cover cards with an IDENTIFIED
        # winner (see aggregates_lib._switch_signal_for_pair) -- add the
        # remainder explicitly so a bar chart of `signal` sums to 100% of
        # decliners instead of silently omitting a (often large) share.
        total_declining = int(signal.n_cards_declining_total.iloc[0])
        identified = int(signal.n_cards.sum())
        unidentified = total_declining - identified
        if unidentified > 0:
            signal = pd.concat([signal, pd.DataFrame([{
                "month_from": int(signal.month_from.iloc[0]),
                "month_to": int(signal.month_to.iloc[0]),
                "n_cards_declining_total": total_declining,
                "destination": "no_clear_destination",
                "n_cards": unidentified,
                "share": unidentified / total_declining,
            }])], ignore_index=True)

    # Switch rate: of cards that were Lidl customers the prior month, the share
    # with ZERO Lidl spend this month (aggregates_lib.build_switch_rate) --
    # independent of whether a destination group could also be identified.
    all_rates = read_out("switch_rate")
    rate_row = all_rates[all_rates.month_to == target] if target is not None and not all_rates.empty else pd.DataFrame()
    switch_rate = None
    switch_rate_detail = None
    if not rate_row.empty:
        r = rate_row.iloc[0]
        switch_rate = round(float(r.switch_rate), 4)
        switch_rate_detail = {
            "n_switched": int(r.n_switched),
            "lidl_customers_prior": int(r.lidl_customers_prior),
            "month_from": int(r.month_from),
            "month_to": int(r.month_to),
        }

    return {
        "city": CONFIG["geography"]["active_city"],
        "signal": records(signal),
        "top_destination": top_destination,
        "switch_rate": switch_rate,
        "switch_rate_detail": switch_rate_detail,
    }


@app.get("/api/customer_profile")
def customer_profile():
    """Every card ever a Lidl customer, segmented as loyal / fading / drifting
    / gone (see aggregates_lib.classify_lidl_segment), profiled by card type
    and spend tier (see aggregates_lib.build_customer_profile). As-of the
    latest month in the panel -- not month-selectable, since the segment
    itself is defined by a card's whole trajectory across all loaded months.
    """
    tiers_df = read_out("spend_tiers")
    tiers = None
    if not tiers_df.empty and pd.notnull(tiers_df.low_max.iloc[0]):
        tiers = {"low_max": float(tiers_df.low_max.iloc[0]), "medium_max": float(tiers_df.medium_max.iloc[0])}

    return {
        "segments": records(read_out("customer_segments")),
        "profile": records(read_out("customer_profile")),
        "spend_tiers": tiers,
    }


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentChatRequest(BaseModel):
    messages: list[AgentMessage]
    month: int | None = None


@app.post("/api/agent/chat")
def agent_chat(req: AgentChatRequest):
    from . import agent

    try:
        reply = agent.chat([m.model_dump() for m in req.messages], req.month)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"reply": reply}
