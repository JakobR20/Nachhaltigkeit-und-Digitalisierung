"""Tests für den geclusterten ARIMA-Detektor (Look-ahead-Schutz, Flag, Exogen)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rausch_energy_anomaly.models.arima_clustered import ArimaClusteredDetector


def _ar1(n: int = 300, phi: float = 0.5, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    e = rng.normal(0, 1, n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + e[t]
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series(y, index=idx)


def _detector() -> ArimaClusteredDetector:
    # AIC-Grid (deterministisch, schnell) statt pmdarima für die Tests
    return ArimaClusteredDetector(use_pmdarima=False, max_p=1, max_q=1, max_d=0, seed=0)


def test_no_lookahead_jump_does_not_affect_earlier_score():
    y = _ar1()
    fit_end = y.index[249]  # Train = erste 250 Punkte
    det = _detector().fit({"g": y.loc[:fit_end]})

    base = y.copy()
    jumped = y.copy()
    jumped.iloc[-1] += 100.0  # Sprung am letzten Punkt t (im Score-Bereich)

    s_base = det.score(base, "g", fit_end=fit_end)
    s_jump = det.score(jumped, "g", fit_end=fit_end)

    # Forecast bei t-1 nutzt nur Daten < t-1 und feste Train-Params -> identisch
    t_minus_1 = y.index[-2]
    assert s_base.loc[t_minus_1, "forecast"] == pytest.approx(s_jump.loc[t_minus_1, "forecast"])
    # Der Sprung selbst schlägt bei t als große Innovation durch
    assert abs(s_jump.loc[y.index[-1], "zscore"]) > 5


def test_clear_jump_is_flagged_normal_point_not():
    y = _ar1()
    fit_end = y.index[249]
    det = _detector().fit({"g": y.loc[:fit_end]})
    jumped = y.copy()
    jumped.iloc[280] += 50.0
    pred = det.predict(jumped, "g", fit_end=fit_end)
    assert pred.loc[y.index[280]] == 1
    assert pred.loc[y.index[260]] == 0


def test_exog_consistent_for_train_and_forecast():
    y = _ar1()
    fit_end = y.index[249]
    det = _detector().fit({"g": y.loc[:fit_end]})
    exog = pd.DataFrame({"is_holiday": np.zeros(len(y))}, index=y.index)
    exog.iloc[290] = 1.0  # ein Feiertag im Forecast-Bereich
    s = det.score(y, "g", fit_end=fit_end, exog=exog)
    assert len(s) == len(y)
    assert (s.index == y.index).all()
    assert s["forecast"].notna().all()


def test_predict_before_fit_raises():
    y = _ar1()
    with pytest.raises(RuntimeError):
        ArimaClusteredDetector().predict(y, "g")


def test_save_load_roundtrip(tmp_path):
    y = _ar1()
    fit_end = y.index[249]
    det = _detector().fit({"g": y.loc[:fit_end]})
    p = tmp_path / "arima.joblib"
    det.save(p)
    loaded = ArimaClusteredDetector.load(p)
    assert loaded.orders_ == det.orders_
