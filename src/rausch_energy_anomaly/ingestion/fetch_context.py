"""Holt Wetter (DWD/Brightsky) und Strompreise (EPEX/energy-charts) für den
Zeitraum der Smart-Meter-Daten und legt sie als Parquet unter data/processed/ ab.

Nutzt die Ingestion-Clients `brightsky.get_weather` / `energy_charts.get_prices`
(mit Cache). Chunkt in 3-Monats-Blöcken, fällt bei API-Problemen pro Block auf
monatlich zurück. Keine Anomalie-Logik – nur Beschaffung, Normalisierung, Sanity-Check.

    python -m rausch_energy_anomaly.ingestion.fetch_context
"""

from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from rausch_energy_anomaly.ingestion import rlm_loader as loader
from rausch_energy_anomaly.ingestion.brightsky import get_weather
from rausch_energy_anomaly.ingestion.energy_charts import get_prices

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_context")

PROCESSED = loader._PROJECT_ROOT / "data" / "processed"
LAT = float(os.getenv("DEFAULT_LAT", "49.7913"))
LON = float(os.getenv("DEFAULT_LON", "9.9534"))
ZONE = os.getenv("DEFAULT_BIDDING_ZONE", "DE-LU")


# --------------------------------------------------------------------------- #
def smart_meter_range(category: str = "Baumärkte") -> tuple[date, date]:
    """Min/Max-Datum über den kompletten geladenen Datensatz der Kategorie."""
    df = loader.load_category(category)
    ts = df.index.get_level_values("timestamp")
    start, end = ts.min().date(), ts.max().date()
    log.info("Zeitraum %s: %s bis %s (%d Zeilen)", category, start, end, len(df))
    return start, end


def _blocks(start: date, end: date, months: int) -> list[tuple[date, date]]:
    """Zerlegt [start, end] in Blöcke à `months` Monaten (inklusiv)."""
    out = []
    cur = pd.Timestamp(start)
    last = pd.Timestamp(end)
    while cur <= last:
        block_end = min(cur + pd.DateOffset(months=months) - pd.Timedelta(days=1), last)
        out.append((cur.date(), block_end.date()))
        cur = block_end + pd.Timedelta(days=1)
    return out


def fetch_chunked(
    fetch_fn, start: date, end: date, label: str, pad_end_days: int = 0
) -> pd.DataFrame:
    """3-Monats-Blöcke; pro Block bei Fehler auf monatlich zurückfallen.

    `pad_end_days` verlängert die angefragte Block-Endgrenze (für DWD nötig:
    Brightsky liefert den `last_date`-Tag nur bis 00:00, sonst fehlen an jeder
    Blockgrenze die Reststunden). Überlappung wird per Dedup bereinigt.
    """
    pad = pd.Timedelta(days=pad_end_days)
    frames = []
    for b_start, b_end in _blocks(start, end, months=3):
        eff_end = (pd.Timestamp(b_end) + pad).date()
        try:
            frames.append(fetch_fn(b_start, eff_end))
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "%s: 3-Monats-Block %s..%s fehlgeschlagen (%s) -> monatlicher Fallback.",
                label,
                b_start,
                b_end,
                exc,
            )
            for m_start, m_end in _blocks(b_start, b_end, months=1):
                m_eff_end = (pd.Timestamp(m_end) + pad).date()
                frames.append(fetch_fn(m_start, m_eff_end))
    df = pd.concat(frames)
    df = df[~df.index.duplicated(keep="first")].sort_index()
    return df


def find_gaps(
    idx: pd.DatetimeIndex, freq: str = "1h"
) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    """Liste fehlender Zeit-Intervalle als (von, bis, anzahl) gegenüber dem Soll-Raster."""
    full = pd.date_range(idx.min(), idx.max(), freq=freq, tz=idx.tz)
    missing = full.difference(idx)
    if len(missing) == 0:
        return []
    step = pd.Timedelta(freq)
    s = missing.to_series()
    run_id = (s.diff() != step).cumsum()
    runs = []
    for _, run in s.groupby(run_id):
        runs.append((run.iloc[0], run.iloc[-1], len(run)))
    return runs


def build_weather_by_site(
    category: str = "Baumärkte",
    out_path: Path | None = None,
) -> pd.DataFrame:
    """Fetch DWD weather per site coordinate and persist as a MultiIndex parquet.

    Coordinates come from ``config/sites.yaml`` (real PLZ centroids). Weather is
    fetched once per unique ``(lat, lon)`` and replicated to every site sharing
    that coordinate, then stored as MultiIndex ``(meter_id, timestamp)`` in
    ``weather_by_site.parquet``. The detection artefacts are weather-independent
    and untouched; only the LLM context layer reads this file.
    """
    out = PROCESSED / "weather_by_site.parquet" if out_path is None else out_path
    sites = loader.load_sites().get("sites", [])
    start, end = smart_meter_range(category)

    coord_cache: dict[tuple[float, float], pd.DataFrame] = {}
    frames = []
    for entry in sites:
        site = loader.resolve_site(entry["id"])
        key = (round(float(site["lat"]), 4), round(float(site["lon"]), 4))
        if key not in coord_cache:
            lat, lon = key
            w = fetch_chunked(
                lambda s, e, lat=lat, lon=lon: get_weather(lat, lon, s, e),
                start, end, f"DWD {entry['id']} {key}", pad_end_days=1,
            )
            w["hdd"] = (15 - w["temperature"]).clip(lower=0)
            coord_cache[key] = w
            log.info("Wetter %s @ %s: %d Stunden", entry["id"], key, len(w))
        frames.append(pd.concat({entry["id"]: coord_cache[key]}, names=["meter_id", "timestamp"]))

    df = pd.concat(frames).sort_index()
    df.to_parquet(out)
    log.info(
        "weather_by_site.parquet: %d Zeilen, %d Sites, %d eindeutige Koordinaten.",
        len(df), len(sites), len(coord_cache),
    )
    return df


def _report_gaps(label: str, idx: pd.DatetimeIndex) -> None:
    gaps = find_gaps(idx)
    if not gaps:
        log.info("%s: keine Zeit-Lücken.", label)
        return
    total = sum(n for *_, n in gaps)
    log.info("%s: %d fehlende Stunden in %d Lücke(n):", label, total, len(gaps))
    for g_start, g_end, n in gaps:
        log.info(
            "  %s: %d fehlende Stunden zwischen %s und %s",
            label,
            n,
            g_start,
            g_end,
        )


# --------------------------------------------------------------------------- #
def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    start, end = smart_meter_range("Baumärkte")

    # Wetter
    weather = fetch_chunked(
        lambda s, e: get_weather(LAT, LON, s, e), start, end, "DWD", pad_end_days=1
    )
    # Heating Degree Days als Feature direkt mitführen
    weather["hdd"] = (15 - weather["temperature"]).clip(lower=0)
    weather.to_parquet(PROCESSED / "weather.parquet")

    # Preise
    prices = fetch_chunked(lambda s, e: get_prices(s, e, ZONE), start, end, "EPEX")
    prices.to_parquet(PROCESSED / "prices.parquet")

    # Sanity-Check
    log.info("--- Sanity-Check ---")
    log.info(
        "weather.parquet: %d Zeilen, %s..%s, temp %.1f..%.1f °C, hdd max %.1f",
        len(weather),
        weather.index.min(),
        weather.index.max(),
        weather["temperature"].min(),
        weather["temperature"].max(),
        weather["hdd"].max(),
    )
    _report_gaps("DWD", weather.index)
    log.info(
        "prices.parquet: %d Zeilen, %s..%s, %.1f..%.1f EUR/MWh",
        len(prices),
        prices.index.min(),
        prices.index.max(),
        prices["price_eur_mwh"].min(),
        prices["price_eur_mwh"].max(),
    )
    _report_gaps("EPEX", prices.index)


if __name__ == "__main__":
    main()
