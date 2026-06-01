"""Deterministic context builder for anomaly recommendations.

``build_minimal_context`` (Phase 2) derives the consumption facts that ground the
LLM prompt — the actual load and the expected load — from the 15-minute RLM source
(``load_category``), NOT from ``features.parquet`` (which is resampled to hourly
for the weather/price merge and would miss the 15-min anomaly timestamps).

Expected load = median of the same weekday + same time-of-day over the preceding
``LOOKBACK_WEEKS`` weeks ("a typical Friday 07:30"). Two edge cases are handled
explicitly because both occur in the real data:

- Few comparison days near the data start: ``n_vergleichstage`` is reported so a
  thin baseline is visible rather than silently trusted.
- Expected load of 0 kW (legitimate at night / when closed): ``diff_pct`` is left
  ``None`` instead of dividing by zero; the prompt formats this as a special case.

``build_full_context`` (Phase 3) adds weather, electricity spot price and a
deterministic excess-cost estimate from the cached parquets (JSON cache is the
documented fallback). Design notes for Phase 3:

- Weather uses a single Würzburg reference station for ALL sites — site PLZ is
  still pending from Rausch, so sites.yaml resolves every site to the Würzburg
  default. This is the real data state, not a silent fallback; the prompt labels
  it as such.
- Spot price is hourly (day-ahead is always hourly); the 15-min anomaly timestamp
  is floored to its hour.
- Excess cost is computed in code, never by the LLM (Phase-1 finding: the model
  does not arithmetic reliably).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from rausch_energy_anomaly.ingestion.rlm_loader import load_category

TZ = "Europe/Berlin"
LOOKBACK_WEEKS = 7
_CATEGORY = "Baumärkte"

_ROOT = Path(__file__).resolve().parents[3]
_WEATHER_PARQUET = _ROOT / "data" / "processed" / "weather.parquet"
_PRICES_PARQUET = _ROOT / "data" / "processed" / "prices.parquet"

# --- unit conversions (parquet stores raw SI / market units) ---
# temperature in weather.parquet is ALREADY °C (verified: range -11.2..36.6).
MS_TO_KMH = 3.6  # wind_speed m/s -> km/h
EUR_PER_MWH_TO_CT_PER_KWH = 0.1  # 1 EUR/MWh = 0.1 ct/kWh

# Bright-Sky `condition` -> German prose for the prompt.
CONDITION_DE = {
    "dry": "trocken",
    "rain": "Regen",
    "sleet": "Schneeregen",
    "snow": "Schnee",
    "fog": "Nebel",
    "hail": "Hagel",
    "thunderstorm": "Gewitter",
}

# Native segment durations for cluster_segment excess-cost (hours).
SEGMENT_DURATION_H = {"nachts": 6.0, "vormittag": 5.0, "mittag": 3.0, "nachmittag": 8.0}
_POINT_METHODS = {"zscore_stl", "arima", "autoencoder"}
_COST_WINDOW_H = 2.0  # ±2h window for point-method duration estimation
_OVERCONSUMPTION_FACTOR = 1.2  # slot counts if value_kw > expected_kw * 1.2
_MAX_DURATION_H = 4.0  # window-bound cap for point-method duration


@dataclass(frozen=True)
class MinimalContext:
    """Deterministic consumption facts for a single anomaly timestamp."""

    site: str
    timestamp: pd.Timestamp
    value_kw: float
    expected_kw: float | None
    diff_kw: float | None
    diff_pct: float | None
    n_vergleichstage: int


@dataclass(frozen=True)
class FullContext:
    """Minimal consumption facts plus weather, spot price and excess cost.

    Weather/price fields are ``None`` when the cache has no record for the hour;
    the prompt layer renders that as an explicit "nicht verfügbar".
    """

    site: str
    timestamp: pd.Timestamp
    method: str
    segment: str
    value_kw: float
    expected_kw: float | None
    diff_kw: float | None
    diff_pct: float | None
    n_vergleichstage: int
    temperatur_c: float | None
    wetter_beschreibung: str | None
    niederschlag_mm: float | None
    windgeschwindigkeit_kmh: float | None
    spotpreis_ct_pro_kwh: float | None
    spotpreis_durchschnitt_24h_ct_pro_kwh: float | None
    dauer_h: float
    mehrkosten_eur: float | None


@lru_cache(maxsize=8)
def _category_values(category: str) -> pd.Series:
    """Load and cache the 15-min value_kw series (MultiIndex meter_id/timestamp)."""
    return load_category(category)["value_kw"]


@lru_cache(maxsize=1)
def _weather_frame() -> pd.DataFrame:
    """Cached weather parquet, index converted to Europe/Berlin."""
    w = pd.read_parquet(_WEATHER_PARQUET)
    w.index = w.index.tz_convert(TZ)
    return w


@lru_cache(maxsize=1)
def _price_series() -> pd.Series:
    """Cached hourly spot-price series (EUR/MWh), index in Europe/Berlin."""
    p = pd.read_parquet(_PRICES_PARQUET)["price_eur_mwh"]
    p.index = p.index.tz_convert(TZ)
    return p


def build_minimal_context(
    site: str,
    timestamp: str | pd.Timestamp,
    category: str = _CATEGORY,
) -> MinimalContext:
    """Build the deterministic minimal context for one anomaly.

    Args:
        site: meter_id, e.g. ``"Baumarkt_06"``.
        timestamp: tz-aware timestamp (string or ``pd.Timestamp``) of the anomaly.
        category: RLM category to load; defaults to Baumärkte.

    Raises:
        KeyError: site not present in the loaded category.
        LookupError: timestamp not present in the site's 15-min series.
    """
    ts = pd.Timestamp(timestamp)
    ts = ts.tz_localize(TZ) if ts.tzinfo is None else ts.tz_convert(TZ)

    series = _category_values(category).xs(site, level="meter_id")

    if ts not in series.index:
        raise LookupError(f"{site}: timestamp {ts} not in 15-min series")
    value_kw = round(float(series.loc[ts]), 3)

    prior = (series.get(ts - pd.Timedelta(weeks=k)) for k in range(1, LOOKBACK_WEEKS + 1))
    comparison = [float(v) for v in prior if v is not None and pd.notna(v)]
    n = len(comparison)

    if n == 0:
        return MinimalContext(site, ts, value_kw, None, None, None, 0)

    expected_kw = round(statistics.median(comparison), 3)
    diff_kw = round(value_kw - expected_kw, 3)
    diff_pct = round(100.0 * diff_kw / expected_kw, 1) if expected_kw != 0 else None
    return MinimalContext(site, ts, value_kw, expected_kw, diff_kw, diff_pct, n)


@dataclass(frozen=True)
class _Weather:
    temperatur_c: float | None = None
    wetter_beschreibung: str | None = None
    niederschlag_mm: float | None = None
    windgeschwindigkeit_kmh: float | None = None


@dataclass(frozen=True)
class _Price:
    spotpreis_ct_pro_kwh: float | None = None
    spotpreis_durchschnitt_24h_ct_pro_kwh: float | None = None


def _r1(v: object) -> float | None:
    return round(float(v), 1) if pd.notna(v) else None  # type: ignore[arg-type]


def _lookup_weather(ts: pd.Timestamp) -> _Weather:
    """Weather at the anomaly hour (Würzburg reference station for all sites).

    Returns an empty ``_Weather`` when the cache has no record for the hour, so the
    caller stays valid and the prompt can say "Wetterdaten nicht verfügbar".
    """
    w = _weather_frame()
    hour = ts.floor("h")
    if hour not in w.index:
        return _Weather()
    row = w.loc[hour]
    if isinstance(row, pd.DataFrame):  # duplicate hour (DST) -> take first
        row = row.iloc[0]
    cond = row["condition"]
    precip = row["precipitation"]
    wind = row["wind_speed"]
    return _Weather(
        temperatur_c=_r1(row["temperature"]),
        wetter_beschreibung=CONDITION_DE.get(cond, cond) if pd.notna(cond) else None,
        niederschlag_mm=round(float(precip), 2) if pd.notna(precip) else None,
        windgeschwindigkeit_kmh=round(float(wind) * MS_TO_KMH, 1) if pd.notna(wind) else None,
    )


def _lookup_price(ts: pd.Timestamp) -> _Price:
    """Hourly spot price at the anomaly hour, plus the trailing 24h mean (ct/kWh).

    Day-ahead prices are hourly, so the 15-min timestamp is floored to its hour.
    Returns an empty ``_Price`` when the hour is outside the cached range.
    """
    p = _price_series()
    hour = ts.floor("h")
    if hour not in p.index:
        return _Price()
    spot_ct = round(float(p.loc[hour]) * EUR_PER_MWH_TO_CT_PER_KWH, 3)
    window = p.loc[hour - pd.Timedelta(hours=23):hour]
    avg_ct = round(float(window.mean()) * EUR_PER_MWH_TO_CT_PER_KWH, 3) if len(window) else None
    return _Price(spotpreis_ct_pro_kwh=spot_ct, spotpreis_durchschnitt_24h_ct_pro_kwh=avg_ct)


def _estimate_duration_h(
    method: str,
    segment: str,
    series: pd.Series,
    ts: pd.Timestamp,
    expected_kw: float | None,
) -> float:
    """Estimate how long the anomaly lasted, in hours.

    - cluster_segment: native segment duration (the method's own granularity).
    - point methods (zscore_stl/arima/autoencoder): count 15-min slots in a ±2h
      window whose load exceeds ``expected_kw * 1.2``; duration = slots * 0.25h,
      clamped to [0.25, 4.0]. If expected is unknown/0, fall back to one slot.
    """
    if method == "cluster_segment":
        return SEGMENT_DURATION_H.get(segment, 0.25)

    if expected_kw is None or expected_kw <= 0:
        return 0.25
    lo = ts - pd.Timedelta(hours=_COST_WINDOW_H)
    hi = ts + pd.Timedelta(hours=_COST_WINDOW_H)
    window = series.loc[lo:hi]
    over = int((window > expected_kw * _OVERCONSUMPTION_FACTOR).sum())
    dauer = over * 0.25
    return max(0.25, min(dauer, _MAX_DURATION_H))


def _estimate_cost_eur(
    diff_kw: float | None, dauer_h: float, spot_ct_per_kwh: float | None
) -> float | None:
    """Excess cost in EUR = diff_kw * dauer_h * price. Underconsumption -> 0.0.

    Returns ``None`` only when the price is unavailable (cost cannot be computed).
    """
    if spot_ct_per_kwh is None or diff_kw is None:
        return None
    if diff_kw <= 0:
        return 0.0  # under-consumption: no excess cost, possible efficiency gain
    price_eur_per_kwh = spot_ct_per_kwh / 100.0
    cost = round(diff_kw * dauer_h * price_eur_per_kwh, 2)
    # A negative spot price yields negative cost (over-consumption is even
    # rewarded); keep the real value but normalise -0.0 to 0.0.
    return cost + 0.0


def build_full_context(
    site: str,
    timestamp: str | pd.Timestamp,
    method: str,
    segment: str,
    category: str = _CATEGORY,
) -> FullContext:
    """Full deterministic context: load facts + weather + price + excess cost.

    Args:
        site: meter_id, e.g. ``"Baumarkt_06"``.
        timestamp: tz-aware timestamp of the anomaly.
        method: detection method (drives the excess-cost duration model).
        segment: daypart segment (used for cluster_segment duration).
        category: RLM category to load; defaults to Baumärkte.

    Raises:
        KeyError / LookupError: see ``build_minimal_context``.
    """
    base = build_minimal_context(site, timestamp, category)
    series = _category_values(category).xs(site, level="meter_id")

    weather = _lookup_weather(base.timestamp)
    price = _lookup_price(base.timestamp)
    dauer_h = _estimate_duration_h(method, segment, series, base.timestamp, base.expected_kw)
    mehrkosten = _estimate_cost_eur(base.diff_kw, dauer_h, price.spotpreis_ct_pro_kwh)

    return FullContext(
        site=base.site,
        timestamp=base.timestamp,
        method=method,
        segment=segment,
        value_kw=base.value_kw,
        expected_kw=base.expected_kw,
        diff_kw=base.diff_kw,
        diff_pct=base.diff_pct,
        n_vergleichstage=base.n_vergleichstage,
        temperatur_c=weather.temperatur_c,
        wetter_beschreibung=weather.wetter_beschreibung,
        niederschlag_mm=weather.niederschlag_mm,
        windgeschwindigkeit_kmh=weather.windgeschwindigkeit_kmh,
        spotpreis_ct_pro_kwh=price.spotpreis_ct_pro_kwh,
        spotpreis_durchschnitt_24h_ct_pro_kwh=price.spotpreis_durchschnitt_24h_ct_pro_kwh,
        dauer_h=dauer_h,
        mehrkosten_eur=mehrkosten,
    )
