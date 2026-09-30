# Wanted — Client Radar

A card-network wallet-intelligence proof of concept for a **Lidl Poland regional director**: which grocery shoppers in Poznań are drifting away from Lidl, where their spend is going instead, and how big that opportunity actually is — built entirely from aggregated Visa card-transaction data.

> Lidl can see its own sales. Only Visa's network data can see where a shopper's wallet goes *after* they stop spending it at Lidl.

## What's in here

- **A data pipeline** (`pipeline/`) that turns raw Visa transaction data into privacy-safe aggregates: wallet share, customer lifecycle segments (loyal/fading/drifting/gone), switch signals, cross-shopping overlap, and customer profiling by card type and spend tier.
- **A FastAPI backend** (`api/`) that serves those aggregates, plus an AI "Market Specialist" chat agent (OpenAI + web search) grounded in the same data.
- **A React/Vite frontend** (`web/`) presenting it all as a guided story: Spotlight → Overview → Profile → Map, with a "Why trust us?" methodology overlay.

## Privacy, by construction

Every number in this app is aggregated across **at least 30 distinct cards** (`k_min` in `config.yaml`) — anything smaller is suppressed automatically. Individual competitor chains are never shown on their own: every competitor number is reported as one of two pooled groups, **discount chains** or **supermarket chains** (their real member chains and market share are disclosed as a static, non-behavioral fact in the "Why trust us?" panel — see `config.yaml`'s `group_info` for how that's computed). No card-level data ever leaves the pipeline.

## Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key (only needed for the Market Specialist chat feature — the rest of the app works without one)

## Setup

```bash
# 1. Python environment (repo root)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Frontend dependencies
cd web && npm install && cd ..

# 3. Environment variables
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...
```

## Running it

The repo ships with the aggregates already built (`data/raw/card_month_4month.csv`, `data/out/*.parquet`), so you can start both servers directly:

```bash
# Terminal 1 — backend (from repo root)
uvicorn api.main:app --port 8000

# Terminal 2 — frontend
cd web && npm run dev
```

Open the URL Vite prints (typically http://localhost:5173).

### Rebuilding the data (optional)

Only needed if you're changing the pipeline logic or config. The raw ~17GB Visa parquet drop is **not** committed to this repo (see `.gitignore`) — place it at `data/raw/datasprint_sample_data.parquet` first, then:

```bash
python pipeline/extract_card_month_csv.py   # raw parquet -> data/raw/card_month_4month.csv
python pipeline/01_panel.py
python pipeline/02_lifecycle.py
python pipeline/03_switching.py
python pipeline/04_aggregates.py            # writes data/out/*.parquet, served by the API
```

`pipeline/00_inspect.py` is a read-only diagnostic script (row/card counts, k-anonymity coverage checks) — run it any time, it changes nothing.

## Tests

```bash
pytest tests/ -q          # Python pipeline logic (57 tests)
cd web && npx tsc -b      # frontend type-check
```

## Project structure

```
config.yaml              # single source of truth: chains, thresholds, privacy k_min
pipeline/                # raw data -> privacy-safe aggregates (DuckDB + pandas)
  extract_card_month_csv.py   # raw Visa parquet -> card-month CSV
  00_inspect.py .. 04_aggregates.py   # numbered phases, run in order
  notebooks/              # exploratory notebook the extraction script replaced
api/
  main.py                 # FastAPI app, reads only data/out/*.parquet
  agent.py                 # Market Specialist chat agent (OpenAI + web search)
data/
  raw/                    # input CSV (tracked) + the raw parquet (gitignored, too large)
  work/, out/             # pipeline intermediate / final aggregates
web/                      # React + TypeScript + Vite + Tailwind + ECharts frontend
tests/                    # pytest suite for the pipeline's pure logic
```

## Scope

This proof of concept covers Poznań only, over a 4-month window (Jan–Apr 2025); the product is designed to scale to any Lidl market and any data window. Cards that vanish from every tracked chain are assumed to have moved away or closed the card, and are excluded from churn.
