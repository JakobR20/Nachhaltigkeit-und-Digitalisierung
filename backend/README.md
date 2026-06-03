# Backend — THWS Energie-Anomalien API

FastAPI service that serves the dashboard data (anomaly list/detail, ensemble
stats, sites) from the existing pipeline artefacts.

## Setup

Dependencies live in the repo-root `pyproject.toml` (shared with the data pipeline).
From the repo root:

```bash
uv sync
```

## Run

```bash
# from the repo root
uvicorn app.main:app --reload --app-dir backend
# or from backend/
cd backend && uvicorn app.main:app --reload
```

API is then at `http://localhost:8000`, interactive docs at `/docs`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/anomalies` | list (params: `site`, `date_from`, `date_to`, `min_cost`, `sort_by`) |
| GET | `/api/anomalies/{nr}` | detail incl. ±3-day load curve |
| GET | `/api/ensemble-stats` | per-method counts + kappa |
| GET | `/api/sites` | 23 sites with anomaly counts |
| GET | `/api/health` | liveness |

CORS is open for `http://localhost:3000` (the Next.js dev server).

## Data sources

- `reports/llm_recommendations/*.json` — cost + cause + context per anomaly
- `reports/annotation/annotation.csv` — `also_flagged_by`
- `data/processed/anomaly_scores.parquet` — ensemble counts
- 15-min load curve via `rausch_energy_anomaly.recommendations.context`

## Tests

```bash
.venv/bin/python -m pytest backend/tests -q
```
