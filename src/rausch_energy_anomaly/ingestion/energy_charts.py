"""
EPEX-SPOT Day-Ahead-Strompreise über die energy-charts API
(Betrieben vom Fraunhofer ISE, kein Key nötig).

Docs: https://api.energy-charts.info/

Wir nutzen /price für Stundenpreise pro Gebotszone.
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

BASE_URL = os.getenv("ENERGY_CHARTS_BASE_URL", "https://api.energy-charts.info")
DEFAULT_ZONE = os.getenv("DEFAULT_BIDDING_ZONE", "DE-LU")
CACHE_DIR = Path(os.getenv("CACHE_DIR", "data/external")) / "epex"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(zone: str, start: date, end: date) -> Path:
    return CACHE_DIR / f"price_{zone}_{start}_{end}.json"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch(zone: str, start: date, end: date) -> dict:
    url = f"{BASE_URL}/price"
    params = {
        "bzn": zone,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
    log.info("EPEX-Request: %s %s", url, params)
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def get_prices(
    start: date | datetime | str,
    end: date | datetime | str,
    zone: str = DEFAULT_ZONE,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Holt stündliche Day-Ahead-Strompreise vom EPEX-SPOT.

    Parameters
    ----------
    start, end : date | datetime | str
        Zeitraum (inklusiv).
    zone : str
        Gebotszone. Default DE-LU (Deutschland-Luxemburg).
    use_cache : bool
        JSON-Cache nutzen.

    Returns
    -------
    pd.DataFrame
        Spalten: timestamp (tz-aware UTC), price_eur_mwh.
    """
    start_d = pd.to_datetime(start).date()
    end_d = pd.to_datetime(end).date()
    cache = _cache_path(zone, start_d, end_d)

    if use_cache and cache.exists():
        log.info("EPEX: lade aus Cache %s", cache.name)
        data = json.loads(cache.read_text())
    else:
        data = _fetch(zone, start_d, end_d)
        cache.write_text(json.dumps(data))
        log.info("EPEX: gecached nach %s", cache.name)

    # energy-charts liefert unix_seconds + price arrays
    if "unix_seconds" not in data or "price" not in data:
        log.warning("Unerwartetes API-Format: %s", list(data.keys()))
        return pd.DataFrame()

    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(data["unix_seconds"], unit="s", utc=True),
            "price_eur_mwh": data["price"],
        }
    )
    return df.set_index("timestamp").sort_index()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    today = date.today()
    df = get_prices(today.replace(day=1), today)
    print(df.head())
    print(f"\n{len(df)} Stunden geladen.")
    if not df.empty:
        print(f"Min: {df['price_eur_mwh'].min():.2f} €/MWh")
        print(f"Max: {df['price_eur_mwh'].max():.2f} €/MWh")
        print(f"Median: {df['price_eur_mwh'].median():.2f} €/MWh")
