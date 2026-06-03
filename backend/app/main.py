"""FastAPI service backing the Next.js dashboard.

Run from the repo root:  uvicorn app.main:app --reload --app-dir backend
or from backend/:         uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import anomalies, stats

app = FastAPI(title="THWS Energie-Anomalien API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(anomalies.router)
app.include_router(stats.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
