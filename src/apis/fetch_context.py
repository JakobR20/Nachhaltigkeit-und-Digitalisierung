"""Holt Wetter (DWD/Brightsky) und Strompreise (EPEX/energy-charts) für den
Zeitraum der Smart-Meter-Daten und legt sie als Parquet unter data/processed/ ab.

Nutzt die bestehenden Clients `src.apis.get_weather` / `get_prices` (mit Cache).
Chunkt in 3-Monats-Blöcken, fällt bei API-Problemen pro Block auf monatlich zurück.
Keine Anomalie-Logik – nur Beschaffung, Normalisierung, Sanity-Check.

    python -m src.apis.fetch_context
"""

from __future__ import annotations

import logging
import os
from datetime import date

import pandas as pd
from dotenv import load_dotenv

from src.apis import get_prices, get_weather
from src.eda import loader

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
