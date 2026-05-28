"""STL-Zerlegung der 15-min-Lastgänge (period=96) – geteilte Vorstufe.

**Eine** Quelle für das saisonbereinigte Signal, die **sowohl** die Z-Score-Baseline
**als auch** ARIMA nutzen (sonst driften die beiden Pfade auseinander). Periode **96**
= Tagesperiode auf 15-min-Basis (24 h × 4). Das alte `features.parquet` (period=168 auf
stündlichen Daten) wird **nicht** wiederverwendet.

Liefert je Zeitpunkt: Trend, Saison, Remainder und die **saison-bereinigte** Reihe
``stl_deseasonalized = trend + remainder`` (= Beobachtung − Saison). ARIMA arbeitet auf
``stl_deseasonalized`` (Trend+Remainder), die Z-Score-Baseline auf ``stl_resid``.
"""
from __future__ import annotations

import pandas as pd
from statsmodels.tsa.seasonal import STL

DEFAULT_PERIOD = 96  # 24 h auf 15-min-Basis


def stl_decompose(
    series: pd.Series,
    period: int = DEFAULT_PERIOD,
    robust: bool = True,
    interpolate_limit: int = 24,
) -> pd.DataFrame:
    """STL-Zerlegung einer **einzelnen** Site-Reihe (15-min, tz-aware).

    Reindext auf das lückenlose 15-min-Raster (STL braucht eine vollständige Reihe),
    interpoliert kurze Lücken (``is_imputed`` markiert sie) und zerlegt.

    Returns
    -------
    DataFrame, Index = timestamp (15-min, tz-aware). Spalten:
    ``value_kw`` (lückengefüllt), ``is_imputed``, ``stl_trend``, ``stl_seasonal``,
    ``stl_resid``, ``stl_deseasonalized`` (= trend + resid).
    """
    s = pd.to_numeric(series, errors="coerce").sort_index()
    full = pd.date_range(s.index.min(), s.index.max(), freq="15min", tz=s.index.tz)
    s = s.reindex(full)
    is_imputed = s.isna()
    s = s.interpolate(limit=interpolate_limit).ffill().bfill()

    res = STL(s, period=period, robust=robust).fit()
    out = pd.DataFrame(
        {
            "value_kw": s.to_numpy(),
            "is_imputed": is_imputed.to_numpy(),
            "stl_trend": res.trend.to_numpy(),
            "stl_seasonal": res.seasonal.to_numpy(),
            "stl_resid": res.resid.to_numpy(),
        },
        index=full,
    )
    out["stl_deseasonalized"] = out["stl_trend"] + out["stl_resid"]
    out.index.name = "timestamp"
    return out
