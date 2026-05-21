"""Unit-Test für den Z-Score-Baseline-Detektor."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.anomaly.zscore import ZScoreDetector


def _series_with_outlier() -> pd.Series:
    rng = np.random.default_rng(42)
    idx = pd.date_range("2024-01-01", periods=10_000, freq="h", tz="Europe/Berlin")
    data = rng.normal(0, 1, size=len(idx))
    data[5000] = 12.0  # klarer Ausreißer
    return pd.Series(data, index=idx)


def test_detects_clear_outlier():
    s = _series_with_outlier()
    det = ZScoreDetector(threshold=3.0).fit(s)
    pred = det.predict(s)
    assert pred.iloc[5000] == 1
    # Z-Score des Ausreißers muss groß sein
    assert det.score(s).iloc[5000] > 8


def test_anomaly_rate_is_small_on_gaussian():
    s = _series_with_outlier()
    det = ZScoreDetector(threshold=3.0).fit(s)
    rate = det.predict(s).mean()
    # Bei ~N(0,1) und |z|>3 erwartet ~0.27 %, mit Toleranz
    assert rate < 0.01


def test_score_preserves_index():
    s = _series_with_outlier()
    z = ZScoreDetector().fit(s).score(s)
    assert z.index.equals(s.index)


def test_raises_when_not_fitted():
    det = ZScoreDetector()
    with pytest.raises(RuntimeError):
        det.score(pd.Series([1.0, 2.0, 3.0]))


def test_raises_on_constant_series():
    det = ZScoreDetector()
    with pytest.raises(ValueError):
        det.fit(pd.Series([5.0] * 100))
