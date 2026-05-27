"""Segment-Aggregat-Features pro Site und Tag (vgl. CLAUDE_patch_v4.md §1.2).

Pro Standort × Tag × Tageszeit-Segment werden Aggregate (mean, max, std, slope)
berechnet. Ergebnis: eine Zeile pro Tag, Spalten ``{segment}_{feature}`` plus je
Segment ein ``{segment}_incomplete``-Flag (DST-/Ausfall-Bewusstsein).

Vektorisiert über ``groupby`` (geschlossene OLS-Form für den Slope) – keine
Tag-für-Tag-Schleife, damit es für ~105k Punkte × N Sites × ~1095 Tage skaliert.
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STEPS_PER_HOUR = 4  # 15-min-Auflösung
_VALID_FEATURES = ("mean", "max", "std", "slope")


def compute_segment_features(
    df: pd.DataFrame,
    site_id: str,
    segments: list[dict],
    features: list[str],
    *,
    value_col: str = "value_kw",
    min_completeness: float = 0.8,
) -> pd.DataFrame:
    """Aggregat-Features je Tag und Tageszeit-Segment für eine Site.

    Parameters
    ----------
    df : 15-min-Lastgang **einer** Site, tz-aware. MultiIndex (meter_id, timestamp)
        oder DatetimeIndex; Wertspalte ``value_col``.
    site_id : nur für Logging.
    segments : Liste aus ``config.yaml`` (``clustering.segmente.segments``), je
        Eintrag ``name``/``start_hour``/``end_hour`` (Halb-offen [start, end)).
    features : Teilmenge von {mean, max, std, slope} (``features_per_segment``).
    value_col : Wertspalte (Default ``value_kw``).
    min_completeness : Anteil erwarteter Punkte, unter dem ein Segment-Tag als
        ``incomplete`` markiert wird (Default 0.8).

    Returns
    -------
    DataFrame, Index = Datum (``datetime.date``), Spalten ``{segment}_{feature}``
    sowie ``{segment}_incomplete`` (bool). NaN, wo ein Segment an einem Tag keine
    (gültigen) Daten hat. Slope in **kW/Stunde**.
    """
    unknown = set(features) - set(_VALID_FEATURES)
    if unknown:
        raise ValueError(f"Unbekannte Features: {sorted(unknown)} (erlaubt: {_VALID_FEATURES})")

    ts = df.index.get_level_values("timestamp") if isinstance(df.index, pd.MultiIndex) else df.index
    seg_names = [s["name"] for s in segments]
    expected = {s["name"]: (s["end_hour"] - s["start_hour"]) * _STEPS_PER_HOUR for s in segments}

    # Segment-Label je Zeitpunkt (halb-offene Fenster). Stunden außerhalb aller
    # Segmente (z. B. 22–24) bleiben ohne Label und fallen heraus.
    segment = pd.Series(pd.NA, index=range(len(ts)), dtype="object")
    hour = ts.hour
    for s in segments:
        mask = (hour >= s["start_hour"]) & (hour < s["end_hour"])
        segment[mask] = s["name"]

    work = pd.DataFrame(
        {
            "date": ts.date,
            "segment": segment.to_numpy(),
            "y": pd.to_numeric(df[value_col], errors="coerce").to_numpy(),
            "x": (hour + ts.minute / 60.0).to_numpy(),  # Stunden-im-Tag -> Slope in kW/h
        }
    ).dropna(subset=["segment", "y"])

    work["xy"] = work["x"] * work["y"]
    work["xx"] = work["x"] * work["x"]

    grouped = work.groupby(["date", "segment"])
    agg = grouped.agg(
        mean=("y", "mean"),
        max=("y", "max"),
        std=("y", "std"),
        n=("y", "count"),
        sx=("x", "sum"),
        sy=("y", "sum"),
        sxy=("xy", "sum"),
        sxx=("xx", "sum"),
    )

    # Slope per geschlossener OLS-Form: (n·Σxy − Σx·Σy) / (n·Σxx − (Σx)²)
    denom = agg["n"] * agg["sxx"] - agg["sx"] ** 2
    slope = (agg["n"] * agg["sxy"] - agg["sx"] * agg["sy"]) / denom
    agg["slope"] = slope.where((agg["n"] >= 2) & (denom != 0))

    # Auf volles (Datum × Segment)-Gitter reindexen, damit fehlende Segmente
    # als NaN/incomplete=True erscheinen statt zu fehlen.
    dates = pd.Index(sorted(work["date"].unique()), name="date")
    full_idx = pd.MultiIndex.from_product([dates, seg_names], names=["date", "segment"])
    agg = agg.reindex(full_idx)
    agg["n"] = agg["n"].fillna(0)
    expected_per_row = agg.index.get_level_values("segment").map(expected)
    agg["incomplete"] = agg["n"] < (min_completeness * pd.Series(expected_per_row, index=agg.index))

    # In Breitformat: je Segment die gewünschten Features + incomplete-Flag.
    out: dict[str, pd.Series] = {}
    for seg_name in seg_names:
        sub = agg.xs(seg_name, level="segment")
        for feat in features:
            out[f"{seg_name}_{feat}"] = sub[feat]
        out[f"{seg_name}_incomplete"] = sub["incomplete"].astype(bool)
    result = pd.DataFrame(out, index=dates).sort_index()

    n_incomplete = int(agg["incomplete"].sum())
    if n_incomplete:
        logger.warning(
            "site=%s: %d Segment-Tag(e) mit <%.0f%% erwarteter Punkte (incomplete=True)",
            site_id,
            n_incomplete,
            min_completeness * 100,
        )
    logger.info(
        "site=%s: %d Tag(e) × %d Segment(e) -> %d Feature-Spalten",
        site_id,
        len(dates),
        len(seg_names),
        result.shape[1],
    )
    return result
