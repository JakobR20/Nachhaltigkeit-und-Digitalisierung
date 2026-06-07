"""Data access for the dashboard API.

Reads the 66 recommendation JSONs (cost + cause + context), annotation.csv (for
also_flagged_by), anomaly_scores.parquet (ensemble counts) and the 15-min load
curve via the existing rausch_energy_anomaly loader. Everything is cached at module
load so requests are fast.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.models.schemas import (
    AnomalyDetail,
    AnomalyListItem,
    Conditions,
    EnsembleStats,
    InferenceCost,
    LoadPoint,
    MethodComparison,
    MethodStat,
    SiteItem,
    SweepPoint,
)
from app.services.cost_calculator import (
    annual_projection,
    build_cost_breakdown,
    is_negative_price,
    is_underconsumption,
)

# repo root = backend/app/services/data_loader.py -> parents[3]
ROOT = Path(__file__).resolve().parents[3]
DETAIL_DIR = ROOT / "reports" / "llm_recommendations"
ANNOTATION = ROOT / "reports" / "annotation" / "annotation.csv"
SCORES = ROOT / "data" / "processed" / "anomaly_scores.parquet"
COMPARISON_MD = ROOT / "reports" / "tables" / "06_method_comparison.md"

METHOD_META = {
    "zscore_stl": ("Z-Score-STL", "Punkt-Anomalien"),
    "arima": ("ARIMA-Forecast", "Vorhersage-Abweichungen"),
    "cluster_segment": ("Cluster-Distanz", "Tagessegmente"),
    "autoencoder": ("Autoencoder", "Formauffälligkeiten"),
}
SPECIAL_SITES = {"Baumarkt_23"}


@functools.lru_cache(maxsize=1)
def _annotation_extra() -> dict[str, list[str]]:
    """nr -> also_flagged_by list (from annotation.csv)."""
    df = pd.read_csv(ANNOTATION, dtype={"nr": str})
    out: dict[str, list[str]] = {}
    for r in df.itertuples():
        raw = getattr(r, "also_flagged_by", "")
        out[r.nr] = [s.strip() for s in str(raw).split(",") if s and str(raw) != "nan"]
    return out


@functools.lru_cache(maxsize=1)
def _all_details() -> list[dict[str, Any]]:
    """Parsed recommendation JSONs, sorted by cost desc."""
    extra = _annotation_extra()
    items = []
    for path in sorted(DETAIL_DIR.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        d["_also_flagged_by"] = extra.get(d["nr"], [])
        items.append(d)
    items.sort(key=lambda d: (d["context"]["mehrkosten_eur"] is not None,
                              d["context"]["mehrkosten_eur"] or 0), reverse=True)
    return items


def _to_list_item(d: dict[str, Any]) -> AnomalyListItem:
    c, r = d["context"], d["recommendation"]
    return AnomalyListItem(
        nr=d["nr"], site=c["site"], timestamp=c["timestamp"], method=c["method"],
        segment=c["segment"], schweregrad=r["schweregrad"], confidence=r["confidence"],
        mehrkosten_eur=c["mehrkosten_eur"],
        jahreskosten_eur=annual_projection(c["mehrkosten_eur"]),
        diff_kw=c["diff_kw"], diff_pct=c["diff_pct"], value_kw=c["value_kw"],
        expected_kw=c["expected_kw"], vermutete_ursache=r["vermutete_ursache"],
        also_flagged_by=d["_also_flagged_by"],
        is_underconsumption=is_underconsumption(c["diff_kw"]),
        is_negative_price=is_negative_price(c["spotpreis_ct_pro_kwh"]),
    )


def list_anomalies(
    site: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_cost: float | None = None,
    sort_by: str = "cost",
) -> list[AnomalyListItem]:
    items = [_to_list_item(d) for d in _all_details()]
    if site:
        items = [i for i in items if i.site == site]
    if date_from:
        lo = pd.Timestamp(date_from, tz="Europe/Berlin")
        items = [i for i in items if pd.Timestamp(i.timestamp) >= lo]
    if date_to:
        hi = pd.Timestamp(date_to, tz="Europe/Berlin")
        items = [i for i in items if pd.Timestamp(i.timestamp) <= hi]
    if min_cost is not None:
        items = [i for i in items if (i.mehrkosten_eur or 0) >= min_cost]

    if sort_by == "date":
        items.sort(key=lambda i: i.timestamp, reverse=True)
    elif sort_by == "severity":
        order = {"hoch": 0, "mittel": 1, "niedrig": 2}
        items.sort(key=lambda i: order.get(i.schweregrad, 9))
    else:  # cost
        items.sort(key=lambda i: (i.mehrkosten_eur is not None, i.mehrkosten_eur or 0),
                   reverse=True)
    return items


FEATURES = ROOT / "data" / "processed" / "features.parquet"


@functools.lru_cache(maxsize=1)
def _load_series() -> pd.Series:
    """Hourly load curve from features.parquet (0.05 s) instead of load_category.

    load_category parses every site Excel (~45 s cold) — far too slow for a request.
    The hourly resolution is plenty for the ±3-day detail plot; the anomaly marker's
    exact value comes from the recommendation JSON, not from this series.
    """
    return pd.read_parquet(FEATURES, columns=["value_kw"])["value_kw"]


def _load_curve(
    site: str, ts: pd.Timestamp, anomaly_value: float | None = None
) -> list[LoadPoint]:
    """±3-day hourly curve, with the exact 15-min anomaly value injected at ts.

    The curve is hourly (fast); a 15-min spike would otherwise be averaged away and
    the marker (which uses the true value_kw) would sit off-chart. Injecting the real
    point keeps the spike visible and the marker on the line.
    """
    series = _load_series().xs(site, level="meter_id")
    win = series[(series.index >= ts - pd.Timedelta(days=3))
                 & (series.index <= ts + pd.Timedelta(days=3))]
    points = {t: round(float(v), 3) for t, v in win.items()}
    if anomaly_value is not None:
        points[ts] = round(float(anomaly_value), 3)  # exact 15-min value at the anomaly
    return [LoadPoint(timestamp=str(t), value_kw=v) for t, v in sorted(points.items())]


def get_anomaly(nr: str) -> AnomalyDetail | None:
    match = next((d for d in _all_details() if d["nr"] == nr), None)
    if match is None:
        return None
    c, r = match["context"], match["recommendation"]
    a = match["annotation"]
    ts = pd.Timestamp(c["timestamp"])
    return AnomalyDetail(
        nr=match["nr"], site=c["site"], timestamp=c["timestamp"], method=c["method"],
        segment=c["segment"], schweregrad=r["schweregrad"],
        vermutete_ursache=r["vermutete_ursache"],
        handlungsempfehlungen=r["handlungsempfehlungen"],
        also_flagged_by=match["_also_flagged_by"],
        cost=build_cost_breakdown(c),
        conditions=Conditions(
            temperatur_c=c["temperatur_c"], wetter_beschreibung=c["wetter_beschreibung"],
            wochentag=a.get("wochentag"), feiertag=a.get("feiertag"),
            confidence=r["confidence"]),
        load_curve=_load_curve(c["site"], ts, c["value_kw"]),
        expected_kw=c["expected_kw"], value_kw=c["value_kw"],
    )


@functools.lru_cache(maxsize=1)
def _kappa() -> dict[str, float]:
    import re

    out: dict[str, float] = {}
    if not COMPARISON_MD.exists():
        return out
    for line in COMPARISON_MD.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3 or cells[1] not in METHOD_META:
            continue
        method = cells[1]
        for cell in cells:
            for other, val in re.findall(r"(\w+)=(-?\d+\.\d+)", cell):
                if other in METHOD_META:
                    out[f"{method}|{other}"] = float(val)
                    out[f"{other}|{method}"] = float(val)
    return out


def ensemble_stats() -> EnsembleStats:
    s = pd.read_parquet(SCORES, columns=["method", "flag"])
    counts = s[s["flag"] == True].groupby("method").size().to_dict()  # noqa: E712
    methods = [
        MethodStat(method=m, label=lbl, description=desc, count=int(counts.get(m, 0)))
        for m, (lbl, desc) in METHOD_META.items()
    ]
    return EnsembleStats(methods=methods, kappa=_kappa())


def list_sites() -> list[SiteItem]:
    s = pd.read_parquet(SCORES, columns=["site", "flag"])
    counts = s[s["flag"] == True].groupby("site").size()  # noqa: E712
    return [SiteItem(site=site, anomaly_count=int(n), is_special=site in SPECIAL_SITES)
            for site, n in counts.items()]


SWEEP_CSV = ROOT / "reports" / "tables" / "06_sweep_flag_rates.csv"


def _inference_costs() -> list[InferenceCost]:
    """Parse Wall-Time fit/score per method from the comparison table."""
    out: list[InferenceCost] = []
    if not COMPARISON_MD.exists():
        return out
    header: list[str] | None = None
    for line in COMPARISON_MD.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if cells and cells[0] == "Methode":
                header = cells
            continue
        if set("".join(cells)) <= {"-", " "} or cells[0] not in METHOD_META:
            continue
        row = dict(zip(header, cells, strict=False))
        try:
            out.append(InferenceCost(
                method=cells[0],
                fit_s=float(row["Wall-Time fit (s)"]),
                score_s=float(row["Wall-Time score (s)"]),
            ))
        except (KeyError, ValueError):
            continue
    return out


def _sweep() -> list[SweepPoint]:
    if not SWEEP_CSV.exists():
        return []
    df = pd.read_csv(SWEEP_CSV)
    return [SweepPoint(**{k: float(v) for k, v in row.items()})
            for row in df.to_dict(orient="records")]


def method_comparison() -> MethodComparison:
    table = COMPARISON_MD.read_text(encoding="utf-8") if COMPARISON_MD.exists() else ""
    return MethodComparison(
        kappa=_kappa(),
        sweep=_sweep(),
        inference=_inference_costs(),
        table_markdown=table,
    )
