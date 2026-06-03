"""Ensemble stats + site list endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import EnsembleStats, MethodComparison, SiteItem
from app.services import data_loader

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/ensemble-stats", response_model=EnsembleStats)
def get_ensemble_stats() -> EnsembleStats:
    return data_loader.ensemble_stats()


@router.get("/sites", response_model=list[SiteItem])
def get_sites() -> list[SiteItem]:
    return data_loader.list_sites()


@router.get("/method-comparison", response_model=MethodComparison)
def get_method_comparison() -> MethodComparison:
    return data_loader.method_comparison()
