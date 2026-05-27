"""Tests für Segment-Aggregat-Features (DST, Slope, Vollständigkeit)."""
from __future__ import annotations

import datetime as dt
import logging

import numpy as np
import pandas as pd
import pytest

from rausch_energy_anomaly.features.segments import compute_segment_features

SEGMENTS = [
    {"name": "nachts", "start_hour": 0, "end_hour": 6},
    {"name": "vormittag", "start_hour": 6, "end_hour": 11},
    {"name": "mittag", "start_hour": 11, "end_hour": 14},
    {"name": "nachmittag", "start_hour": 14, "end_hour": 22},
]
FEATURES = ["mean", "max", "std", "slope"]


def _day_index(day: str = "2024-06-03") -> pd.DatetimeIndex:
    """Normaler Tag (kein DST-Übergang) im 15-min-Raster, Europe/Berlin."""
    return pd.date_range(f"{day} 00:00", f"{day} 23:45", freq="15min", tz="Europe/Berlin")


def _df(index: pd.DatetimeIndex, values) -> pd.DataFrame:
    return pd.DataFrame({"value_kw": values}, index=index)


def test_columns_and_one_row_per_day():
    idx = _day_index()
    res = compute_segment_features(_df(idx, 10.0), "s1", SEGMENTS, FEATURES)
    assert len(res) == 1
    for seg in ("nachts", "vormittag", "mittag", "nachmittag"):
        for feat in FEATURES:
            assert f"{seg}_{feat}" in res.columns
        assert f"{seg}_incomplete" in res.columns


def test_slope_in_kw_per_hour():
    idx = _day_index()
    # value = 2 kW pro Stunde linear -> Slope = 2.0 in jedem Segment
    values = 2.0 * (idx.hour + idx.minute / 60.0)
    res = compute_segment_features(_df(idx, values), "s1", SEGMENTS, FEATURES)
    d = dt.date(2024, 6, 3)
    for seg in ("nachts", "vormittag", "mittag", "nachmittag"):
        assert res.loc[d, f"{seg}_slope"] == pytest.approx(2.0, abs=1e-6)


def test_full_segment_missing_returns_nan_no_crash():
    idx = _day_index()
    keep = ~((idx.hour >= 14) & (idx.hour < 22))  # nachmittag komplett entfernen
    idx2 = idx[keep]
    res = compute_segment_features(_df(idx2, 5.0), "s1", SEGMENTS, FEATURES)
    d = dt.date(2024, 6, 3)
    assert np.isnan(res.loc[d, "nachmittag_mean"])
    assert bool(res.loc[d, "nachmittag_incomplete"]) is True
    # andere Segmente intakt
    assert res.loc[d, "nachts_mean"] == 5.0


def test_incomplete_flag_below_threshold(caplog):
    idx = _day_index()
    nachts_first4 = idx[(idx.hour == 0) & (idx.minute < 60)][:4]  # nur 4 von 24
    rest = idx[idx.hour >= 6]
    idx2 = nachts_first4.append(rest)
    with caplog.at_level(logging.WARNING):
        res = compute_segment_features(_df(idx2, 7.0), "s1", SEGMENTS, FEATURES)
    d = dt.date(2024, 6, 3)
    assert bool(res.loc[d, "nachts_incomplete"]) is True
    assert bool(res.loc[d, "vormittag_incomplete"]) is False
    assert "site=s1" in caplog.text and "incomplete=True" in caplog.text


def test_dst_spring_day_is_kept():
    # 2024-03-31: Frühjahrs-Umstellung, 02:00–02:59 existiert nicht -> nachts hat 20/24 Punkte
    idx = pd.date_range(
        "2024-03-31 00:00", "2024-03-31 23:45", freq="15min", tz="Europe/Berlin"
    )
    res = compute_segment_features(_df(idx, 1.0), "s1", SEGMENTS, FEATURES)
    d = dt.date(2024, 3, 31)
    assert d in res.index
    assert res.loc[d, "nachts_mean"] == 1.0          # berechnet, nicht verworfen
    assert bool(res.loc[d, "nachts_incomplete"]) is False  # 20/24 = 83% >= 80%


def test_dst_fall_duplicate_is_robust():
    # Herbst-Duplikat simulieren: nachts-Stunde 02:00–02:45 zusätzlich (28 statt 24 Punkte)
    idx = _day_index("2024-10-27")
    extra = idx[(idx.hour == 2)]
    idx2 = idx.append(extra)
    res = compute_segment_features(_df(idx2, 5.0), "s1", SEGMENTS, FEATURES)
    d = dt.date(2024, 10, 27)
    assert res.loc[d, "nachts_mean"] == 5.0                 # Aggregat robust
    assert bool(res.loc[d, "nachts_incomplete"]) is False   # mehr Punkte als erwartet


def test_unknown_feature_raises():
    idx = _day_index()
    with pytest.raises(ValueError):
        compute_segment_features(_df(idx, 1.0), "s1", SEGMENTS, ["median"])
