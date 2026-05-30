"""Export der Top-Anomalie-Kandidaten je Methode als CSV + Plots für die Annotation.

Liest ``data/processed/anomaly_scores.parquet`` (alle drei Methoden) und
``data/processed/segment_features.parquet`` (für den Incomplete-Filter pro
Segment-Tag), wählt Top-20 |score| je Methode, entfernt Duplikate auf
``(site, timestamp)`` mit Priorität ``zscore_stl > arima > cluster_segment``
und schreibt nach ``reports/annotation/``:

- ``plot_{nr:03d}.png`` – ±3 Tage Kontext-Lastgang mit roter Markierung
  (vertikale Linie/Marker bei Punkt-Methoden, Segment-Band bei
  ``cluster_segment``)
- ``annotation.csv`` – Reviewer-Liste mit leeren Spalten ``label``/``notiz``
- ``README.md`` – Annotations-Anleitung (drei Labels)

Ausführung::

    .venv/bin/python -m rausch_energy_anomaly.evaluation.export_annotation
"""

from __future__ import annotations

import logging
from pathlib import Path

import holidays
import matplotlib

matplotlib.use("Agg")  # bewusst VOR dem pyplot-Import: headless, kein DISPLAY nötig
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from rausch_energy_anomaly.ingestion import rlm_loader  # noqa: E402

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
_SCORES = _ROOT / "data" / "processed" / "anomaly_scores.parquet"
_SEG_FEATURES = _ROOT / "data" / "processed" / "segment_features.parquet"
_OUT = _ROOT / "reports" / "annotation"

SEGMENT_HOURS: dict[str, tuple[int, int]] = {
    "nachts": (0, 6),
    "vormittag": (6, 11),
    "mittag": (11, 14),
    "nachmittag": (14, 22),
}
METHOD_PRIORITY = {"zscore_stl": 0, "arima": 1, "cluster_segment": 2, "autoencoder": 3}
EXCLUDE_SITES: tuple[str, ...] = ("Baumarkt_23",)
N_PER_METHOD = 20
CONTEXT_DAYS = 3


def _segment_of_hour(hour: int) -> str | None:
    """Segment-Name für eine Stunde 0..23, oder ``None`` für 22..24."""
    for name, (start, end) in SEGMENT_HOURS.items():
        if start <= hour < end:
            return name
    return None


def _derive_segment(row: pd.Series) -> str | None:
    if row["method"] == "cluster_segment":
        return row["segment"]
    return _segment_of_hour(row["timestamp"].hour)


def select_candidates(scores: pd.DataFrame, n_per_method: int = N_PER_METHOD) -> pd.DataFrame:
    """Top-N |score| je Methode → drop_duplicates(site,timestamp) nach Prioritätsordnung."""
    # NaN-Scores raus (ARIMA hat Boundary-NaNs, AE-DST-Lücken sind NaN by design)
    scores = scores[scores["score"].notna()]
    work = scores.assign(abs_score=scores["score"].abs())
    work["rang_in_methode"] = (
        work.groupby("method")["abs_score"].rank(method="first", ascending=False).astype(int)
    )
    top = work[work["rang_in_methode"] <= n_per_method].copy()

    # also_flagged_by: andere Methoden mit identischem (site, timestamp) im Top-N
    by_key = top.groupby(["site", "timestamp"])["method"].apply(list).to_dict()

    top["_priority"] = top["method"].map(METHOD_PRIORITY)
    top = (
        top.sort_values(["site", "timestamp", "_priority"])
        .drop_duplicates(subset=["site", "timestamp"], keep="first")
        .drop(columns="_priority")
    )
    top["also_flagged_by"] = top.apply(
        lambda r: ",".join(m for m in by_key[(r["site"], r["timestamp"])] if m != r["method"]),
        axis=1,
    )
    return top.reset_index(drop=True)


def filter_incomplete(candidates: pd.DataFrame, seg_features: pd.DataFrame) -> pd.DataFrame:
    """Wirft Kandidaten, deren (site, date, segment) in ``seg_features`` incomplete ist.

    Kandidaten in Stunden 22..24 (kein Segment) bleiben drin — sie können nicht
    "incomplete" sein, weil sie zu keinem Segment gehören. (site, date)-Lücken im
    Segment-Features-Parquet werden konservativ als incomplete behandelt.
    """
    keep = []
    for _, row in candidates.iterrows():
        seg_name = _derive_segment(row)
        if seg_name is None:
            keep.append(True)
            continue
        date = row["timestamp"].date()
        try:
            incomplete = bool(seg_features.loc[(row["site"], date), f"{seg_name}_incomplete"])
        except KeyError:
            incomplete = True
        keep.append(not incomplete)
    return candidates[pd.Series(keep, index=candidates.index)].reset_index(drop=True)


def _holiday_dates() -> set:
    return set(holidays.Germany(years=[2023, 2024, 2025], state="BY").keys())


def build_plot(
    series_window: pd.Series,
    candidate: pd.Series,
    plot_path: Path,
    rang: int,
    is_holiday: bool,
) -> None:
    """±3-Tage-Lastgang um den Kandidaten, rote Markierung an der Anomalie-Stelle."""
    t = candidate["timestamp"]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series_window.index, series_window.to_numpy(), color="steelblue", linewidth=0.8)

    if candidate["method"] == "cluster_segment":
        seg_name = candidate["segment"]
        start_h, end_h = SEGMENT_HOURS[seg_name]
        day = pd.Timestamp(t.date(), tz=t.tz)
        ax.axvspan(
            day + pd.Timedelta(hours=start_h),
            day + pd.Timedelta(hours=end_h),
            alpha=0.25,
            color="red",
            label=f"Segment {seg_name}",
        )
        ax.legend(loc="upper right", fontsize=8)
    else:
        ax.axvline(t, color="red", alpha=0.6, linewidth=1)
        if t in series_window.index:
            ax.plot([t], [series_window.loc[t]], "ro", markersize=5)

    title = (
        f"Site={candidate['site']} | {t.date()} | Methode={candidate['method']} | "
        f"Score-Rang im Methoden-Top-20: {rang} | {t.day_name()} | "
        f"Feiertag={'ja' if is_holiday else 'nein'}"
    )
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Zeitstempel (Europe/Berlin)")
    ax.set_ylabel("Lastgang [kW]")
    fig.autofmt_xdate()
    fig.savefig(plot_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


_README = """# Annotation der Top-Anomalie-Kandidaten

Felix & Jakob, bitte die ~60 Kandidaten in `annotation.csv` durchgehen und in den
beiden hinteren Spalten `label` und `notiz` füllen.

## Labels (genau einer pro Zeile)

- **`plausibel_anomal`** — sieht im Kontextfenster (±3 Tage) tatsächlich nach
  unerwartetem Verhalten aus, das eine Rückfrage beim Betreiber rechtfertigt
  (durchlaufende Nachtbasis, fehlender Tagesgang, abrupter Niveaubruch).
- **`erklärbar`** — der Ausschlag ist im Lastgang sichtbar, hat aber eine
  plausible Erklärung, die KEINE Anomalie ist (Feiertag, Wartung,
  Inbetriebnahme, Wetterspitze, Inventur).
- **`unklar`** — aus den ±3 Tagen Kontext nicht zuordenbar; im Notizfeld die
  offene Frage festhalten.

## Workflow

1. PNG zur jeweiligen `nr` öffnen (`plot_001.png` …).
2. Label in `annotation.csv` setzen, optional Notiz.
3. Bei Unsicherheit: `unklar` + Begründung in `notiz`.

## Spalten

- `nr` — laufende Nummer, korrespondiert zu `plot_{nr:03d}.png`.
- `site`, `timestamp`, `method`, `score` — Anomalie-Identifikation.
- `rang_in_methode` — Rang innerhalb der Top-20 dieser Methode (1 = höchster
  |score|). Score-Werte sind zwischen Methoden NICHT direkt vergleichbar
  (unterschiedliche Skalen) — deshalb der Rang als methoden-interner Bezug.
- `segment` — Segment des Tages (`nachts` / `vormittag` / `mittag` /
  `nachmittag`); bei Punkt-Methoden aus der Stunde abgeleitet.
- `wochentag`, `feiertag` — aus dem Zeitstempel (Feiertage Bayern).
- `also_flagged_by` — andere Methoden, die denselben `(site, timestamp)` in
  ihren Top-20 hatten (methoden-übergreifende Auffälligkeit).
- `plot_datei` — Dateiname des Kontext-Plots.
- `label`, `notiz` — **leer; wird von euch ausgefüllt.**
"""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    _OUT.mkdir(parents=True, exist_ok=True)

    logger.info("Lade %s", _SCORES.relative_to(_ROOT))
    scores = pd.read_parquet(_SCORES)
    scores = scores[~scores["site"].isin(EXCLUDE_SITES)].copy()
    logger.info("scores: %d Zeilen, %d Sites", len(scores), scores["site"].nunique())

    seg_features = pd.read_parquet(_SEG_FEATURES)

    logger.info("Wähle Top-%d je Methode, prioritäts-deduplizieren ...", N_PER_METHOD)
    candidates = select_candidates(scores, n_per_method=N_PER_METHOD)
    logger.info("Vor incomplete-Filter: %d Kandidaten", len(candidates))
    candidates = filter_incomplete(candidates, seg_features)
    logger.info(
        "Nach incomplete-Filter: %d Kandidaten (pro Methode: %s)",
        len(candidates),
        candidates["method"].value_counts().to_dict(),
    )

    logger.info("Lade Lastgang-Kategorie (~45 s) ...")
    df = rlm_loader.load_category("Baumärkte")

    hol = _holiday_dates()

    rows: list[dict] = []
    for nr, (_, c) in enumerate(candidates.iterrows(), start=1):
        site = c["site"]
        t = c["timestamp"]
        series = df.xs(site, level="meter_id")["value_kw"]
        window = series.loc[
            t - pd.Timedelta(days=CONTEXT_DAYS) : t + pd.Timedelta(days=CONTEXT_DAYS)
        ]
        plot_name = f"plot_{nr:03d}.png"
        is_holiday = t.date() in hol
        build_plot(
            window, c, _OUT / plot_name, rang=int(c["rang_in_methode"]), is_holiday=is_holiday
        )
        rows.append(
            {
                "nr": nr,
                "site": site,
                "timestamp": t,
                "method": c["method"],
                "score": float(c["score"]),
                "rang_in_methode": int(c["rang_in_methode"]),
                "segment": _derive_segment(c) or "",
                "wochentag": t.day_name(),
                "feiertag": "ja" if is_holiday else "nein",
                "plot_datei": plot_name,
                "also_flagged_by": c["also_flagged_by"],
                "label": "",
                "notiz": "",
            }
        )
        if nr % 10 == 0:
            logger.info("Plots: %d / %d", nr, len(candidates))

    out_csv = _OUT / "annotation.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    (_OUT / "README.md").write_text(_README, encoding="utf-8")
    logger.info(
        "Fertig: %d Plots + %s + README.md in %s",
        len(rows),
        out_csv.name,
        _OUT.relative_to(_ROOT),
    )


def append_autoencoder_candidates(
    annotation_csv: Path | None = None, n_per_method: int = N_PER_METHOD
) -> int:
    """Append AE-Top-Kandidaten an die bestehende ``annotation.csv`` (idempotent).

    Bestehende Zeilen werden NICHT überschrieben (auch nicht ``also_flagged_by``);
    die Funktion hängt ausschließlich neue AE-Kandidaten an, deren
    ``(site, timestamp)`` noch nicht in der CSV ist. Plots werden mit fortlaufender
    ``nr`` (ab ``len(existing) + 1``) erzeugt.

    Returns die Anzahl neu angehängter Zeilen.
    """
    import csv

    path = Path(annotation_csv) if annotation_csv is not None else (_OUT / "annotation.csv")
    if not path.exists():
        raise FileNotFoundError(f"annotation.csv fehlt: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    existing = rows[1:]
    site_idx, ts_idx = header.index("site"), header.index("timestamp")
    existing_keys = {(r[site_idx], pd.Timestamp(r[ts_idx])) for r in existing}
    next_nr = len(existing) + 1

    logger.info("Lade %s + %s", _SCORES.name, _SEG_FEATURES.name)
    scores = pd.read_parquet(_SCORES)
    scores = scores[~scores["site"].isin(EXCLUDE_SITES)].copy()
    seg_features = pd.read_parquet(_SEG_FEATURES)

    deduped = select_candidates(scores, n_per_method=n_per_method)
    deduped = filter_incomplete(deduped, seg_features)

    ae = deduped[deduped["method"] == "autoencoder"].reset_index(drop=True)
    new_mask = ae.apply(lambda r: (r["site"], r["timestamp"]) not in existing_keys, axis=1)
    new = ae[new_mask].reset_index(drop=True)
    logger.info(
        "AE-Top-%d nach Prioritäts-Dedup: %d Zeilen; nach existing-Filter: %d neu",
        n_per_method,
        len(ae),
        len(new),
    )
    if not len(new):
        return 0

    logger.info("Lade Lastgang-Kategorie (~45 s) ...")
    df = rlm_loader.load_category("Baumärkte")
    hol = _holiday_dates()

    appended_rows: list[list[str]] = []
    for offset, (_, c) in enumerate(new.iterrows(), start=0):
        nr = next_nr + offset
        site = c["site"]
        t = c["timestamp"]
        series = df.xs(site, level="meter_id")["value_kw"]
        window = series.loc[
            t - pd.Timedelta(days=CONTEXT_DAYS) : t + pd.Timedelta(days=CONTEXT_DAYS)
        ]
        plot_name = f"plot_{nr:03d}.png"
        is_holiday = t.date() in hol
        build_plot(
            window, c, _OUT / plot_name, rang=int(c["rang_in_methode"]), is_holiday=is_holiday
        )
        appended_rows.append(
            [
                str(nr),
                site,
                t.isoformat() if hasattr(t, "isoformat") else str(t),
                c["method"],
                repr(float(c["score"])),
                str(int(c["rang_in_methode"])),
                _derive_segment(c) or "",
                t.day_name(),
                "ja" if is_holiday else "nein",
                plot_name,
                c["also_flagged_by"],
                "",
                "",
            ]
        )

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        for row in appended_rows:
            w.writerow(row)

    logger.info(
        "appended %d AE-Kandidaten (nr %d..%d) an %s",
        len(appended_rows),
        next_nr,
        next_nr + len(appended_rows) - 1,
        path.relative_to(_ROOT),
    )
    return len(appended_rows)


if __name__ == "__main__":
    main()
