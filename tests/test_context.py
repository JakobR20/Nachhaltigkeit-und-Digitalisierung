"""Tests for the full context builder (Phase 3).

The real RLM Excels are gitignored, so these tests never call the real loaders:
synthetic value/weather/price data is injected via the module's lru_cache'd
accessors. That keeps the tests fast and runnable without the confidential data.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from rausch_energy_anomaly.recommendations import context as ctx_mod
from rausch_energy_anomaly.recommendations.context import (
    FullContext,
    _estimate_cost_eur,
    _estimate_duration_h,
    build_full_context,
)
from rausch_energy_anomaly.recommendations.prompts import render_user_prompt

TZ = "Europe/Berlin"
SITE = "Baumarkt_TEST"
ANOMALY_TS = pd.Timestamp("2024-05-08 02:00", tz=TZ)


@pytest.fixture
def synthetic_caches(monkeypatch):
    """Inject synthetic value/weather/price series into the cached accessors.

    value: 10 weeks of 15-min data at ~8 kW baseline, with a 72 kW spike at the
    anomaly timestamp and its ±2h neighbours elevated, so the duration estimator
    has something to count.
    """
    start = ANOMALY_TS - pd.Timedelta(weeks=9)
    end = ANOMALY_TS + pd.Timedelta(weeks=1)
    idx = pd.date_range(start, end, freq="15min", tz=TZ)
    s = pd.Series(8.0, index=idx, name="value_kw")
    s.loc[ANOMALY_TS] = 72.6
    # elevate a few neighbouring slots (> 8 * 1.2) within ±2h
    for k in range(1, 5):
        s.loc[ANOMALY_TS + pd.Timedelta(minutes=15 * k)] = 40.0
    multi = pd.concat({SITE: s}, names=["meter_id", "timestamp"])
    monkeypatch.setattr(ctx_mod, "_category_values", lambda category: multi)

    widx = pd.date_range(start, end, freq="h", tz=TZ)
    weather = pd.DataFrame(
        {
            "temperature": np.full(len(widx), 10.5),
            "condition": "rain",
            "precipitation": 0.0,
            "wind_speed": 5.0,
        },
        index=widx,
    )
    monkeypatch.setattr(ctx_mod, "_weather_frame", lambda: weather)

    price = pd.Series(80.0, index=widx, name="price_eur_mwh")  # 80 EUR/MWh = 8 ct/kWh
    monkeypatch.setattr(ctx_mod, "_price_series", lambda: price)
    return s


def test_build_full_context_returns_all_fields(synthetic_caches):
    c = build_full_context(SITE, ANOMALY_TS, "cluster_segment", "nachts")
    assert isinstance(c, FullContext)
    # every dataclass field is populated (no field left unset)
    for f in dataclasses.fields(FullContext):
        assert hasattr(c, f.name)
    assert c.value_kw == pytest.approx(72.6)
    assert c.expected_kw == pytest.approx(8.0)
    assert c.temperatur_c == pytest.approx(10.5)
    assert c.wetter_beschreibung == "Regen"
    assert c.windgeschwindigkeit_kmh == pytest.approx(18.0)  # 5 m/s * 3.6
    assert c.spotpreis_ct_pro_kwh == pytest.approx(8.0)
    assert c.mehrkosten_eur is not None


def test_build_full_context_handles_missing_weather(synthetic_caches, monkeypatch):
    # weather frame without the anomaly hour -> all weather fields None
    empty = pd.DataFrame(
        columns=["temperature", "condition", "precipitation", "wind_speed"],
        index=pd.DatetimeIndex([], tz=TZ),
    )
    monkeypatch.setattr(ctx_mod, "_weather_frame", lambda: empty)
    c = build_full_context(SITE, ANOMALY_TS, "arima", "nachts")
    assert c.temperatur_c is None
    assert c.wetter_beschreibung is None
    assert c.niederschlag_mm is None
    assert c.windgeschwindigkeit_kmh is None
    # context stays valid: load + price fields still present
    assert c.value_kw == pytest.approx(72.6)
    assert c.spotpreis_ct_pro_kwh is not None


def test_mehrkosten_negative_diff_returns_zero():
    # under-consumption: no excess cost regardless of price
    assert _estimate_cost_eur(diff_kw=-6.6, dauer_h=3.0, spot_ct_per_kwh=11.0) == 0.0


def test_mehrkosten_none_price_returns_none():
    assert _estimate_cost_eur(diff_kw=64.6, dauer_h=6.0, spot_ct_per_kwh=None) is None


def test_mehrkosten_cluster_segment_uses_segment_duration():
    # cluster_segment 'nachts' -> 6h duration, independent of the load window
    dummy = pd.Series(dtype=float)
    assert _estimate_duration_h("cluster_segment", "nachts", dummy, ANOMALY_TS, 8.0) == 6.0
    assert _estimate_duration_h("cluster_segment", "nachmittag", dummy, ANOMALY_TS, 8.0) == 8.0


def test_point_method_duration_counts_overconsumption_slots(synthetic_caches):
    series = synthetic_caches
    # 4 elevated neighbour slots (40 kW > 8*1.2) + the anomaly slot itself = 5 -> 1.25h
    dauer = _estimate_duration_h("arima", "nachts", series, ANOMALY_TS, 8.0)
    assert dauer == pytest.approx(1.25)


def test_point_method_duration_zero_expected_falls_back_to_one_slot():
    dummy = pd.Series(dtype=float)
    assert _estimate_duration_h("arima", "vormittag", dummy, ANOMALY_TS, 0.0) == 0.25


def _ctx_with_price(spotpreis_ct: float) -> FullContext:
    """Minimal FullContext fixed to a given spot price for render tests."""
    return FullContext(
        site=SITE, timestamp=ANOMALY_TS, method="arima", segment="nachts",
        value_kw=72.6, expected_kw=8.0, diff_kw=64.6, diff_pct=807.5,
        n_vergleichstage=7, temperatur_c=10.0, wetter_beschreibung="trocken",
        niederschlag_mm=0.0, windgeschwindigkeit_kmh=5.0,
        spotpreis_ct_pro_kwh=spotpreis_ct,
        spotpreis_durchschnitt_24h_ct_pro_kwh=9.0,
        dauer_h=0.25, mehrkosten_eur=1.0,
    )


def test_render_user_prompt_negative_price_adds_context():
    prompt = render_user_prompt(_ctx_with_price(-0.5))
    assert "Spotpreis ist negativ" in prompt
    assert "belohnt" in prompt


def test_render_user_prompt_high_price_adds_context():
    prompt = render_user_prompt(_ctx_with_price(25.0))
    assert "Spotpreis ist hoch" in prompt
    assert "besonders teuer" in prompt


def test_render_user_prompt_normal_price_no_context():
    prompt = render_user_prompt(_ctx_with_price(8.0))
    assert "Spotpreis ist negativ" not in prompt
    assert "Spotpreis ist hoch" not in prompt
