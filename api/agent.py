"""Market Specialist chat agent.

Wraps the OpenAI Responses API with two sources of grounding: (1) this
platform's own pooled aggregates -- reusing the same functions main.py's
endpoints call, so the agent can never see anything an API caller couldn't
already fetch -- and (2) OpenAI's built-in web_search tool for live context
on the active city. Individual competitor chain names are never available to
the model: every aggregate here is already pooled to {hero, discounts,
supermarket} before it reaches this module.
"""
import datetime
import json
import os
import pathlib
import re

from dotenv import load_dotenv
from openai import APIStatusError, OpenAI

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

_client: OpenAI | None = None


def get_client() -> OpenAI | None:
    global _client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You are the Market Specialist inside Wanted (Client Radar), a card-network wallet-intelligence tool built for a Lidl Poland regional director.

Ground every claim in the PLATFORM DATA below. It comes from real Visa card-transaction aggregates for {city}, already privacy-safe: individual competitor chains are never revealed, only pooled "discount chains" and "supermarket chains" groups. Never name or guess at a specific competitor chain, and never invent numbers that aren't in PLATFORM DATA or returned by your own web search.

Use the web_search tool to bring in current, real context about {city} (local economy, retail news, population and consumer trends, new store openings, etc.) when the question calls for it -- but PLATFORM DATA is always the primary evidence for anything about Lidl's own customers.

Answer only the question actually asked, as briefly as that question allows. A factual or descriptive question (e.g. "what's the economic situation in {city}?") gets a short, direct answer -- do not pad it with PLATFORM DATA figures, a recommendation, or a forced multi-part structure unless the question actually calls for that. Save the fuller "explanation + external context + recommendation" treatment for questions that are actually asking what the data means or what to do about it.

Be concise and business-focused: this is for a retail director's decision-making, not a data scientist. Avoid jargon like "k-anonymity" or "pooled group" -- say "discount chains" / "supermarket chains" plainly.

Today's real-world date is {today}. That is for your own grounding (e.g. interpreting how recent a web search result is) only -- it has nothing to do with the data below.

PLATFORM DATA (JSON, historical, currently viewing month {month} -- a YYYYMM code, e.g. 202504 means April 2025):
{context_json}
"""


def _strip_utm_source_openai(text: str) -> str:
    """OpenAI's web_search tool appends ?utm_source=openai to every citation
    URL it returns -- strip it (whether it's the only query param or one of
    several) so links stay clean when the director wants to open a source."""
    text = re.sub(r"([?&])utm_source=openai&", r"\1", text)
    return re.sub(r"[?&]utm_source=openai\b", "", text)


def build_context(month: int | None) -> dict:
    # Deferred import: main.py imports this module lazily inside its request
    # handler (long after main.py itself has finished loading), so by the
    # time this runs api.main is fully initialized -- no circularity.
    from .main import customer_profile, meta, overlap, overview, poznan

    meta_data = meta()
    overview_data = overview()
    months_covered = meta_data["months_covered"]
    target_month = month if month is not None else (months_covered[-1] if months_covered else None)

    return {
        "selected_month": target_month,
        "meta": meta_data,
        "overview_kpis": overview_data["kpis"],
        "wallet_share_all_months": overview_data["wallet_share"],
        "overlap_this_month": overlap(target_month) if target_month is not None else [],
        "switch_signal_this_month": poznan(target_month) if target_month is not None else {},
        "customer_profile": customer_profile(),
    }


def chat(messages: list[dict], month: int | None) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to a .env file at the project root.")

    context = build_context(month)
    city = context["meta"]["active_city"]
    system_prompt = SYSTEM_PROMPT.format(
        city=city,
        month=context["selected_month"],
        today=datetime.date.today().isoformat(),
        context_json=json.dumps(context, default=str),
    )

    try:
        response = client.responses.create(
            model="gpt-5",
            instructions=system_prompt,
            input=[{"role": m["role"], "content": m["content"]} for m in messages],
            tools=[
                {
                    "type": "web_search",
                    "user_location": {"type": "approximate", "city": city, "country": "PL"},
                }
            ],
        )
    except APIStatusError as e:
        # Surface OpenAI's own message (billing, quota, invalid key, etc.)
        # instead of a bare 500 -- these are account issues, not bugs.
        detail = getattr(e, "message", None) or str(e)
        raise RuntimeError(f"OpenAI API error: {detail}") from e

    return _strip_utm_source_openai(response.output_text.strip())
