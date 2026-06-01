"""Deterministic context builder for anomaly recommendations (Phase 2, minimal).

``build_minimal_context`` derives the consumption facts that ground the LLM
prompt — the actual load and the expected load — from the 15-minute RLM source
(``load_category``), NOT from ``features.parquet`` (which is resampled to hourly
for the weather/price merge and would miss the 15-min anomaly timestamps).

Expected load = median of the same weekday + same time-of-day over the preceding
``LOOKBACK_WEEKS`` weeks ("a typical Friday 07:30"). Two edge cases are handled
explicitly because both occur in the real data:

- Few comparison days near the data start: ``n_vergleichstage`` is reported so a
  thin baseline is visible rather than silently trusted.
- Expected load of 0 kW (legitimate at night / when closed): ``diff_pct`` is left
  ``None`` instead of dividing by zero; the prompt formats this as a special case.

Weather, price and excess-cost fields are deliberately NOT built here — they are
Phase 3 and rendered as ``<Phase 3>`` placeholders by the prompt layer.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from rausch_energy_anomaly.ingestion.rlm_loader import load_category

TZ = "Europe/Berlin"
LOOKBACK_WEEKS = 7
_CATEGORY = "Baumärkte"


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


@lru_cache(maxsize=8)
def _category_values(category: str) -> pd.Series:
    """Load and cache the 15-min value_kw series (MultiIndex meter_id/timestamp)."""
    return load_category(category)["value_kw"]


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
