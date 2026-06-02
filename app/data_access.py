"""Cached data-access layer shared by all dashboard pages.

Every loader is wrapped in ``st.cache_data`` so a parquet is read once per session
and reused across page switches. Loaders read only the columns they need (lazy),
since anomaly_scores.parquet has ~6.7M rows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "data" / "processed" / "anomaly_scores.parquet"
LLM_CSV = ROOT / "reports" / "llm_recommendations.csv"
ANNOTATION = ROOT / "reports" / "annotation" / "annotation.csv"
DASHBOARD_YAML = ROOT / "config" / "dashboard.yaml"
COMPARISON_MD = ROOT / "reports" / "tables" / "06_method_comparison.md"

METHODS = ("zscore_stl", "arima", "cluster_segment", "autoencoder")


@st.cache_data
def load_config() -> dict[str, Any]:
    with open(DASHBOARD_YAML) as f:
        cfg: dict[str, Any] = yaml.safe_load(f)
    return cfg


@st.cache_data
def load_flag_matrix() -> pd.DataFrame:
    """Flagged-anomaly counts per site x method (one row per site)."""
    s = pd.read_parquet(SCORES, columns=["site", "method", "flag"])
    flagged = s[s["flag"] == True]  # noqa: E712 - pandas boolean mask
    matrix = flagged.groupby(["site", "method"]).size().unstack(fill_value=0)
    for m in METHODS:
        if m not in matrix.columns:
            matrix[m] = 0
    matrix = matrix[list(METHODS)]
    matrix["gesamt"] = matrix.sum(axis=1)
    return matrix.reset_index()


@st.cache_data
def load_recommendations() -> pd.DataFrame:
    """LLM recommendations table (66 annotated anomalies)."""
    df = pd.read_csv(LLM_CSV, dtype={"nr": str})
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    return df


@st.cache_data
def load_annotation() -> pd.DataFrame:
    return pd.read_csv(ANNOTATION, dtype={"nr": str})


@st.cache_data
def load_site_timeseries(site: str) -> pd.Series:
    """15-min load curve for one site, from the RLM source (lazy, per site)."""
    from rausch_energy_anomaly.recommendations.context import _category_values

    return _category_values("Baumärkte").xs(site, level="meter_id")


@st.cache_data
def load_scores_for_site(site: str) -> pd.DataFrame:
    """All method scores/flags for one site (lazy filter on the big parquet)."""
    s = pd.read_parquet(SCORES)
    return s[s["site"] == site].copy()


@st.cache_data
def load_comparison_markdown() -> str:
    return COMPARISON_MD.read_text(encoding="utf-8") if COMPARISON_MD.exists() else ""


@st.cache_data
def load_sweep() -> pd.DataFrame:
    """X-sweep flag rates (% per method over threshold_pct), precomputed CSV."""
    path = COMPARISON_MD.parent / "06_sweep_flag_rates.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data
def expected_profile(site: str) -> pd.Series:
    """Expected load profile: median per (weekday, time-of-day) over full history.

    Indexed by (dayofweek, time) so a window can be mapped to its expectation.
    """
    s = load_site_timeseries(site)
    return s.groupby([s.index.dayofweek, s.index.time]).median()


@st.cache_data
def annotated_index() -> dict[tuple[str, str], dict[str, str]]:
    """{(site, timestamp_str): {nr, schweregrad}} for the 66 annotated anomalies."""
    recs = load_recommendations()
    return {(r.site, str(r.timestamp)): {"nr": r.nr, "schweregrad": r.schweregrad}
            for r in recs.itertuples()}


@st.cache_data
def load_cost_table() -> pd.DataFrame:
    """One row per annotated anomaly with cost + context fields, from the 66 JSONs.

    This is the data source for the cost-first anomaly list/detail pages. Sorted by
    estimated extra cost descending (None costs last).
    """
    import json

    detail_dir = ROOT / "reports" / "llm_recommendations"
    rows = []
    for path in sorted(detail_dir.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        c, r, a = d["context"], d["recommendation"], d["annotation"]
        rows.append({
            "nr": d["nr"], "site": c["site"], "timestamp": c["timestamp"],
            "method": c["method"], "segment": c["segment"],
            "mehrkosten_eur": c["mehrkosten_eur"], "diff_kw": c["diff_kw"],
            "diff_pct": c["diff_pct"], "value_kw": c["value_kw"],
            "expected_kw": c["expected_kw"], "dauer_h": c["dauer_h"],
            "spotpreis_ct": c["spotpreis_ct_pro_kwh"],
            "temperatur_c": c["temperatur_c"], "wetter": c["wetter_beschreibung"],
            "schweregrad": r["schweregrad"], "confidence": r["confidence"],
            "vermutete_ursache": r["vermutete_ursache"],
            "feiertag": a["feiertag"], "wochentag": a["wochentag"],
        })
    df = pd.DataFrame(rows)
    return df.sort_values("mehrkosten_eur", ascending=False, na_position="last")


@st.cache_data
def load_recommendation_detail(nr: str) -> dict[str, Any]:
    """Full per-anomaly JSON (context + prompt + response) for the detail page."""
    import json

    path = ROOT / "reports" / "llm_recommendations" / f"{int(nr):03d}.json"
    detail: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return detail


def sites() -> list[str]:
    return sorted(load_flag_matrix()["site"].tolist())
