"""
DWD-Wetterdaten via Brightsky (offizieller, gut dokumentierter DWD-Wrapper).

Brightsky bietet historische und Forecast-Daten ohne API-Key.
Docs: https://brightsky.dev/docs/

Wir nutzen den /weather Endpunkt für stündliche Werte.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
log = logging.getLogger(__name__)

BASE_URL = os.getenv("DWD_BASE_URL", "https://api.brightsky.dev")
CACHE_DIR = Path(os.getenv("CACHE_DIR", "data/raw")) / "weather"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(lat: float, lon: float, start: date, end: date) -> Path:
    key = f"weather_{lat:.4f}_{lon:.4f}_{start}_{end}.json"
    return CACHE_DIR / key


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch(lat: float, lon: float, start: date, end: date) -> dict:
    url = f"{BASE_URL}/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "date": start.isoformat(),
        "last_date": end.isoformat(),
        "units": "si",  # SI: Temperatur in KELVIN, Wind m/s, Strahlung W/m²
    }
    log.info("DWD-Request: %s %s", url, params)
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def get_weather(
    lat: float,
    lon: float,
    start: date | datetime | str,
    end: date | datetime | str,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Holt stündliche Wetterdaten vom DWD (via Brightsky).

    Parameters
    ----------
    lat, lon : float
        Koordinaten der Station / des Standorts.
    start, end : date | datetime | str
        Zeitraum (inklusiv). Strings müssen ISO-Format sein.
    use_cache : bool
        Wenn True (Default), wird ein lokaler JSON-Cache genutzt.

    Returns
    -------
    pd.DataFrame
        Index: timestamp (tz-aware UTC). Spalten u. a.:
        temperature, dew_point, wind_speed, wind_direction,
        cloud_cover, precipitation, sunshine, condition.
    """
    start_d = pd.to_datetime(start).date()
    end_d = pd.to_datetime(end).date()
    cache = _cache_path(lat, lon, start_d, end_d)

    if use_cache and cache.exists():
        log.info("DWD: lade aus Cache %s", cache.name)
        data = json.loads(cache.read_text())
    else:
        data = _fetch(lat, lon, start_d, end_d)
        cache.write_text(json.dumps(data))
        log.info("DWD: gecached nach %s", cache.name)

    df = pd.DataFrame(data["weather"])
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").sort_index()
    # Brightsky liefert mit units=si Temperaturen in Kelvin -> auf °C bringen,
    # damit der dokumentierte Vertrag (°C) und Features wie HDD stimmen.
    for col in ("temperature", "dew_point"):
        if col in df.columns:
            df[col] = df[col] - 273.15
    return df


if __name__ == "__main__":
    # Kleiner Smoke-Test: Würzburg, letzte 7 Tage
    logging.basicConfig(level=logging.INFO)
    today = date.today()
    df = get_weather(49.7913, 9.9534, today.replace(day=1), today)
    print(df.head())
    print(f"\n{len(df)} Stunden geladen.")
    print(f"Spalten: {list(df.columns)}")
