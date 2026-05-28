"""Tests für die geteilte 15-min-STL-Zerlegung (period=96)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from rausch_energy_anomaly.features.stl_decompose import DEFAULT_PERIOD, stl_decompose


def _synth(days: int = 30, seed: int = 0) -> pd.Series:
    """Trend + Tages-Saison (period=96) + Rauschen, 15-min, Europe/Berlin."""
    n = days * 96
    idx = pd.date_range("2024-01-01 00:00", periods=n, freq="15min", tz="Europe/Berlin")
    t = np.arange(n)
    trend = 10 + 0.001 * t
    seasonal = 5 * np.sin(2 * np.pi * (t % 96) / 96)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.2, n)
    return pd.Series(trend + seasonal + noise, index=idx, name="value_kw")


def test_default_period_is_96():
    assert DEFAULT_PERIOD == 96


def test_reconstruction_and_deseasonalized_identity():
    s = _synth()
    out = stl_decompose(s)
    # STL ist additiv: trend + seasonal + resid == value
    recon = out["stl_trend"] + out["stl_seasonal"] + out["stl_resid"]
    assert np.allclose(recon.to_numpy(), out["value_kw"].to_numpy(), atol=1e-6)
    # deseasonalized == trend + resid == value - seasonal
    assert np.allclose(
        out["stl_deseasonalized"].to_numpy(),
        (out["value_kw"] - out["stl_seasonal"]).to_numpy(),
        atol=1e-6,
    )
    assert (
        not out[["stl_trend", "stl_seasonal", "stl_resid", "stl_deseasonalized"]].isna().any().any()
    )


def test_seasonal_component_captures_daily_cycle():
    s = _synth()
    out = stl_decompose(s)
    # Die Saison-Amplitude (~5) sollte deutlich größer sein als die Remainder-Streuung
    assert out["stl_seasonal"].std() > 3 * out["stl_resid"].std()


def test_gaps_are_filled_and_flagged():
    s = _synth()
    s_gap = s.drop(s.index[200:210])  # 10 Punkte entfernen
    out = stl_decompose(s_gap)
    # lückenloses Raster, keine NaN, und die entfernten Stellen sind als imputiert markiert
    assert out["stl_resid"].notna().all()
    assert bool(out["is_imputed"].iloc[200:210].all()) is True
    assert int(out["is_imputed"].sum()) >= 10
