"""Pydantic response schemas for the dashboard API."""

from __future__ import annotations

from pydantic import BaseModel


class AnomalyListItem(BaseModel):
    """One row in the cost-prioritised anomaly list."""

    nr: str
    site: str
    timestamp: str
    method: str
    segment: str
    schweregrad: str
    confidence: float
    mehrkosten_eur: float | None
    jahreskosten_eur: float | None
    diff_kw: float | None
    diff_pct: float | None
    value_kw: float | None
    expected_kw: float | None
    vermutete_ursache: str
    also_flagged_by: list[str]
    # flags steering the frontend's alternative rendering
    is_underconsumption: bool
    is_negative_price: bool


class LoadPoint(BaseModel):
    timestamp: str
    value_kw: float
    expected_kw: float | None = None


class CostBreakdown(BaseModel):
    diff_kw: float | None
    dauer_h: float
    diff_kwh: float | None
    spotpreis_ct: float | None
    mehrkosten_eur: float | None
    jahreskosten_eur: float | None
    is_underconsumption: bool
    is_negative_price: bool


class Conditions(BaseModel):
    temperatur_c: float | None
    wetter_beschreibung: str | None
    wochentag: str | None
    feiertag: str | None
    confidence: float


class AnomalyDetail(BaseModel):
    """Full detail for one anomaly, including the load curve window."""

    nr: str
    site: str
    timestamp: str
    method: str
    segment: str
    schweregrad: str
    vermutete_ursache: str
    handlungsempfehlungen: list[str]
    also_flagged_by: list[str]
    cost: CostBreakdown
    conditions: Conditions
    load_curve: list[LoadPoint]
    expected_kw: float | None
    value_kw: float | None


class MethodStat(BaseModel):
    method: str
    label: str
    description: str
    count: int


class EnsembleStats(BaseModel):
    methods: list[MethodStat]
    kappa: dict[str, float]  # "a|b" -> kappa


class SiteItem(BaseModel):
    site: str
    anomaly_count: int
    is_special: bool


class SweepPoint(BaseModel):
    threshold_pct: float
    arima: float | None = None
    autoencoder: float | None = None
    cluster_segment: float | None = None
    zscore_stl: float | None = None


class InferenceCost(BaseModel):
    method: str
    fit_s: float
    score_s: float


class MethodComparison(BaseModel):
    kappa: dict[str, float]
    sweep: list[SweepPoint]
    inference: list[InferenceCost]
    table_markdown: str
