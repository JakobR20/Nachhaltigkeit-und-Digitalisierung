"""Anomaly list + detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import AnomalyDetail, AnomalyListItem
from app.services import data_loader

router = APIRouter(prefix="/api", tags=["anomalies"])


@router.get("/anomalies", response_model=list[AnomalyListItem])
def get_anomalies(
    site: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_cost: float | None = None,
    sort_by: str = "cost",
) -> list[AnomalyListItem]:
    return data_loader.list_anomalies(site, date_from, date_to, min_cost, sort_by)


@router.get("/anomalies/{nr}", response_model=AnomalyDetail)
def get_anomaly_detail(nr: str) -> AnomalyDetail:
    detail = data_loader.get_anomaly(nr)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"anomaly {nr} not found")
    return detail
