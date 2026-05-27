"""
Wiederverwendbare Hilfsfunktionen für die explorative Datenanalyse (EDA)
von Smart-Meter-Zeitreihen.

Diese Funktionen sind absichtlich format-agnostisch, weil wir das genaue Schema
der RAUSCH-Daten noch nicht kennen. Sobald wir es kennen, kann das `load_*`
spezialisiert werden.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd


def load_smartmeter(
    path: str | Path,
    timestamp_col: str | None = None,
    value_col: str | None = None,
    meter_id_col: str | None = None,
    tz: str = "Europe/Berlin",
) -> pd.DataFrame:
    """
    Liest Smart-Meter-Daten aus CSV oder Parquet.

    Versucht das Format automatisch zu erkennen. Wenn die Spaltennamen
    abweichen, bitte explizit übergeben.

    Returns
    -------
    DataFrame mit MultiIndex (meter_id, timestamp) und Spalte 'value'.
    """
    path = Path(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unbekanntes Format: {path.suffix}")

    # Heuristische Spaltenerkennung – Claude Code soll das nach erster EDA anpassen.
    if timestamp_col is None:
        for c in ("timestamp", "datetime", "time", "Zeitstempel", "ts"):
            if c in df.columns:
                timestamp_col = c
                break
    if value_col is None:
        for c in ("value", "consumption", "kwh", "verbrauch", "energy", "Wert"):
            if c in df.columns:
                value_col = c
                break
    if meter_id_col is None:
        for c in ("meter_id", "zaehler_id", "id", "device_id"):
            if c in df.columns:
                meter_id_col = c
                break

    if timestamp_col is None or value_col is None:
        raise ValueError(
            f"Spalten nicht erkannt. Gefunden: {list(df.columns)}. "
            "Bitte timestamp_col / value_col explizit angeben."
        )

    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    # Auf Berlin-Zeit lokalisieren, falls naiv. Sonst belassen.
    if df[timestamp_col].dt.tz is None:
        df[timestamp_col] = df[timestamp_col].dt.tz_localize(tz, ambiguous="infer")

    if meter_id_col is None:
        df["meter_id"] = "single_meter"
        meter_id_col = "meter_id"

    df = df.rename(columns={timestamp_col: "timestamp", value_col: "value"})
    return (
        df[[meter_id_col, "timestamp", "value"]]
        .rename(columns={meter_id_col: "meter_id"})
        .set_index(["meter_id", "timestamp"])
        .sort_index()
    )


def detect_resolution(s: pd.Series) -> pd.Timedelta:
    """Schätzt die Sampling-Auflösung einer Zeitreihe (Median der Diffs)."""
    if isinstance(s.index, pd.MultiIndex):
        first_meter = s.index.get_level_values(0)[0]
        s = s.loc[first_meter]
    diffs = s.index.to_series().diff().dropna()
    return diffs.median()


def basic_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ein-Zeilen-Profil pro Zähler: Anzahl, Min, Max, Mean, Std, Anteil NaN,
    Zeitraum, Auflösung.
    """
    rows = []
    for meter_id, g in df.groupby(level="meter_id"):
        s = g["value"]
        idx = s.index.get_level_values("timestamp")
        rows.append(
            {
                "meter_id": meter_id,
                "n": len(s),
                "n_missing": int(s.isna().sum()),
                "missing_pct": float(s.isna().mean() * 100),
                "min": float(s.min()),
                "max": float(s.max()),
                "mean": float(s.mean()),
                "std": float(s.std()),
                "start": idx.min(),
                "end": idx.max(),
                "duration_days": (idx.max() - idx.min()).days,
                "resolution_min": detect_resolution(s).total_seconds() / 60,
            }
        )
    return pd.DataFrame(rows).set_index("meter_id")


def to_hourly(df: pd.DataFrame, agg: Literal["sum", "mean"] = "mean") -> pd.DataFrame:
    """Aggregiert auf Stundenbasis. 'sum' für Energie (kWh), 'mean' für Leistung (kW)."""
    out = []
    for meter_id, g in df.groupby(level="meter_id"):
        s = g["value"].droplevel("meter_id")
        s_h = s.resample("1h").agg(agg)
        s_h = s_h.to_frame("value")
        s_h["meter_id"] = meter_id
        out.append(s_h.set_index("meter_id", append=True).swaplevel().sort_index())
    return pd.concat(out)


def add_calendar_features(df: pd.DataFrame, timestamp_level: str = "timestamp") -> pd.DataFrame:
    """Fügt Kalender-Features hinzu: hour, dow, is_weekend, month, doy."""
    df = df.copy()
    ts = df.index.get_level_values(timestamp_level)
    df["hour"] = ts.hour
    df["dow"] = ts.dayofweek  # 0=Mo, 6=So
    df["is_weekend"] = (ts.dayofweek >= 5).astype(int)
    df["month"] = ts.month
    df["doy"] = ts.dayofyear
    return df


def rolling_zscore(s: pd.Series, window: str = "7D", min_periods: int = 24) -> pd.Series:
    """
    Rolling Z-Score. Anomalie typischerweise wenn |z| > 3.
    Window als Pandas-Offset, z.B. "7D" für 7 Tage.
    """
    mean = s.rolling(window, min_periods=min_periods).mean()
    std = s.rolling(window, min_periods=min_periods).std()
    return (s - mean) / std.replace(0, np.nan)
