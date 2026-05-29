"""End-to-End-Scoring der drei Methoden in ein gemeinsames, NATIVES Format.

Drei Ebenen bewusst getrennt:
- **Speichern (hier):** native Granularität. Z-Score/ARIMA pro 15-min-Punkt
  (``granularity="point"``, ``segment=None``); Cluster-Distanz pro Segment-Tag
  (``granularity="segment_day"``, ``segment`` gesetzt). **Kein** Broadcast in der Quelle.
- **Vergleichen:** :func:`to_segment_day_grid` aggregiert die Punkt-Methoden **hoch**
  auf ``(site, date, segment)`` (Kappa/Overlap auf der gröbsten gemeinsamen Granularität).
- **Anzeigen:** Broadcast nur im Plot (Notebook), nicht im Storage.

Gemeinsames Schema (`anomaly_scores.parquet`):
``site, timestamp, method, score, flag, granularity, segment``.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import yaml

from rausch_energy_anomaly.features.stl_decompose import stl_decompose
from rausch_energy_anomaly.ingestion import rlm_loader as loader
from rausch_energy_anomaly.models.arima_clustered import ArimaClusteredDetector
from rausch_energy_anomaly.models.baseline_zscore import ZScoreDetector
from rausch_energy_anomaly.models.clustering_daily import DailyProfileClusterer
from rausch_energy_anomaly.models.clustering_segments import SegmentClusterer

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA = ["site", "timestamp", "method", "score", "flag", "granularity", "segment"]


def _load_config(path: str | Path | None = None) -> dict:
    path = Path(path) if path else _ROOT / "config" / "config.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _site_mean_profile(series: pd.Series) -> pd.Series:
    """96-dim mittleres Tagesprofil (Slot 0..95) einer Site."""
    ts = series.index
    slot = ts.hour * 4 + ts.minute // 15
    prof = pd.Series(series.to_numpy(), index=slot).groupby(level=0).mean()
    return prof.reindex(range(96))


def _point_rows(site: str, score: pd.Series, flag: pd.Series, method: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "site": site,
            "timestamp": score.index,
            "method": method,
            "score": score.to_numpy(dtype=float),
            "flag": flag.to_numpy(dtype=bool),
            "granularity": "point",
            "segment": pd.NA,
        }
    )


def run_all_methods(
    category: str = "Baumärkte",
    sites: list[str] | None = None,
    config_path: str | Path | None = None,
    write: bool = True,
    order_search_points: int = 20000,
) -> pd.DataFrame:
    """Scort Z-Score, ARIMA und Cluster-Distanz auf echten Daten -> gemeinsames Schema."""
    cfg = _load_config(config_path)
    period = cfg["models"]["zscore"]["stl_period"]
    z_thr = cfg["models"]["zscore"]["threshold"]
    # tz-aware Jahresende 2024 (Train-Slice 2023–2024) für die 15-min-Reihen (ARIMA)
    train_end = pd.Timestamp("2024-12-31 23:45", tz="Europe/Berlin")
    train_end_date = pd.Timestamp("2024-12-31").date()  # date-Variante für Segment-Tag-Vergleich
    seg_defs = cfg["clustering"]["segmente"]["segments"]
    seg_names = [s["name"] for s in seg_defs]
    seg_start = {s["name"]: s["start_hour"] for s in seg_defs}
    features = cfg["clustering"]["segmente"]["features_per_segment"]
    k_seg = cfg["clustering"]["segmente"]["k_final_per_segment"]
    thr_pct = cfg["clustering"]["segmente"]["distance_threshold_percentile"]
    k_daily = cfg["clustering"]["tagesprofile"]["k_final"]

    df = loader.load_category(category)
    vmax = df.groupby(level="meter_id")["value_kw"].max()
    solid = sorted(vmax[vmax >= 1.0].index)
    sites = sites or solid
    logger.info("Scoring %s: %d Site(s)", category, len(sites))

    # Geteilte STL-Stufe (period=96) je Site – Quelle für Z-Score UND ARIMA.
    stl = {s: stl_decompose(df.xs(s, level="meter_id")["value_kw"], period=period) for s in sites}

    frames: list[pd.DataFrame] = []

    # 1) Z-Score auf stl_resid
    for s in sites:
        z = ZScoreDetector(threshold=z_thr).fit(stl[s]["stl_resid"]).score(stl[s]["stl_resid"])
        frames.append(_point_rows(s, z, z.abs() > z_thr, "zscore_stl"))

    # 2) ARIMA pro Peer-Gruppe (auf stl_deseasonalized), pro Site angewandt
    profiles = pd.DataFrame(
        {s: _site_mean_profile(df.xs(s, level="meter_id")["value_kw"]) for s in sites}
    ).T
    profiles = profiles.apply(lambda col: col.fillna(profiles.mean(axis=1)))
    labels = DailyProfileClusterer(k=min(k_daily, len(sites))).fit(profiles).labels_
    repr_by_group: dict = {}
    for g in sorted(labels.unique()):
        members = labels[labels == g].index
        mat = pd.concat([stl[m]["stl_deseasonalized"] for m in members], axis=1)
        repr_by_group[g] = mat.mean(axis=1).dropna()
    # Ordnungssuche auf begrenztem, auflösungs-konsistentem Fenster (Tempo;
    # die Ordnung ist robust gegen die genaue Länge). Scoring nutzt die volle Reihe.
    arima = ArimaClusteredDetector().fit(
        {g: s.iloc[-order_search_points:] for g, s in repr_by_group.items()}
    )
    for s in sites:
        sc = arima.score(stl[s]["stl_deseasonalized"], group=labels[s], fit_end=train_end)
        z = sc["zscore"]
        frames.append(_point_rows(s, z, z.abs() > z_thr, "arima"))

    # 3) Cluster-Distanz pro Segment-Tag (nativ segment_day)
    seg = pd.read_parquet(_ROOT / "data" / "processed" / "segment_features.parquet")
    seg = seg.loc[seg.index.get_level_values("site").isin(sites)]
    seg_dates = seg.index.get_level_values("date")
    train_mask = pd.Series([d <= train_end_date for d in seg_dates], index=seg.index)
    sclu = SegmentClusterer(seg_names, features, k_seg, threshold_percentile=thr_pct).fit(
        seg, train_mask
    )
    dist = sclu.score(seg)
    pred = sclu.predict(seg)
    for name in seg_names:
        idx = seg.index
        site_arr = idx.get_level_values("site")
        date_arr = idx.get_level_values("date")
        ts = pd.to_datetime(pd.Series(date_arr)) + pd.to_timedelta(seg_start[name], unit="h")
        frames.append(
            pd.DataFrame(
                {
                    "site": site_arr,
                    "timestamp": ts.to_numpy(),
                    "method": "cluster_segment",
                    "score": dist[f"{name}_distance"].to_numpy(dtype=float),
                    "flag": pred[f"{name}_anomaly"].to_numpy(dtype=bool),
                    "granularity": "segment_day",
                    "segment": name,
                }
            )
        )

    out = pd.concat(frames, ignore_index=True)[_SCHEMA]
    if write:
        path = _ROOT / "data" / "processed" / "anomaly_scores.parquet"
        out.to_parquet(path, index=False)
        logger.info("geschrieben: %s (%d Zeilen)", path, len(out))
    return out


def _setup_autoencoder(
    category: str,
    sites: list[str] | None,
    exclude: tuple[str, ...],
    variant: str,
    fit_end: pd.Timestamp,
    **detector_kwargs: object,
):
    """Lädt Kategorie, filtert Sites (vmax≥1 kW, ohne ``exclude``), fittet den AE.

    Liefert ``(detector, series_by_site, sites)``. Wiederverwendbar für Stage-B-
    Anomalie-Injection (gleicher gefitteter Detector, ohne Re-Train).
    """
    from rausch_energy_anomaly.models.autoencoder import AutoencoderDetector

    df = loader.load_category(category)
    vmax = df.groupby(level="meter_id")["value_kw"].max()
    solid = sorted(vmax[vmax >= 1.0].index)
    sites = [s for s in (sites or solid) if s not in exclude]
    logger.info(
        "AE-Setup %s: %d Site(s) (variant=%s, exclude=%s)", category, len(sites), variant, exclude
    )
    series_by_site = {s: df.xs(s, level="meter_id")["value_kw"] for s in sites}
    det = AutoencoderDetector(variant=variant, **detector_kwargs).fit(
        series_by_site, fit_end=fit_end
    )
    return det, series_by_site, sites


def run_autoencoder(
    category: str = "Baumärkte",
    sites: list[str] | None = None,
    exclude: tuple[str, ...] = ("Baumarkt_23",),
    variant: str = "dense",
    config_path: str | Path | None = None,  # noqa: ARG001  (Schema-Symmetrie zu run_all_methods)
    write: bool = True,
    fit_end: pd.Timestamp | None = None,
    **detector_kwargs: object,
) -> pd.DataFrame:
    """Scort den per-Kategorie-Autoencoder ins gemeinsame native Format.

    Native: ``granularity="point"``, ``segment=None``, ``method="autoencoder"``.
    DST-/Teiltage erscheinen explizit als NaN-Zeilen (``score=NaN``, ``flag=pd.NA``),
    damit Schritt 11 „kein Score" sauber von „Score=0" trennt. Sites in ``exclude``
    (Default: Baumarkt_23 – nur 2025-Daten → leerer Train-Slice) entfallen vor fit().
    Bei ``write=True`` werden bestehende ``method=="autoencoder"``-Zeilen im Parquet
    durch den neuen Lauf ersetzt (idempotent).
    """
    if fit_end is None:
        fit_end = pd.Timestamp("2024-12-31 23:45", tz="Europe/Berlin")

    det, series_by_site, sites = _setup_autoencoder(
        category, sites, exclude, variant, fit_end, **detector_kwargs
    )

    frames: list[pd.DataFrame] = []
    for s in sites:
        series = series_by_site[s]
        err = det.score(series, s)  # nur volle 96-Slot-Tage
        err_full = err.reindex(series.index)  # NaN an DST-/Teiltagen
        flag = pd.array([pd.NA] * len(err_full), dtype="boolean")
        valid = err_full.notna().to_numpy()
        flag[valid] = err_full.to_numpy()[valid] > det.threshold_
        frames.append(
            pd.DataFrame(
                {
                    "site": s,
                    "timestamp": err_full.index,
                    "method": "autoencoder",
                    "score": err_full.to_numpy(dtype=float),
                    "flag": flag,
                    "granularity": "point",
                    "segment": pd.NA,
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)[_SCHEMA]

    if write:
        path = _ROOT / "data" / "processed" / "anomaly_scores.parquet"
        if path.exists():
            existing = pd.read_parquet(path)
            existing = existing[existing["method"] != "autoencoder"].copy()
            existing["flag"] = existing["flag"].astype("boolean")
            combined = pd.concat([existing, out], ignore_index=True)[_SCHEMA]
        else:
            combined = out
        combined.to_parquet(path, index=False)
        logger.info("geschrieben: %s (%d AE-Zeilen, %d gesamt)", path, len(out), len(combined))
    return out


# --------------------------------------------------------------------------- #
# Vergleich: HOCH-Aggregation auf (site, date, segment)
# --------------------------------------------------------------------------- #
def to_segment_day_grid(
    scores: pd.DataFrame, config_path: str | Path | None = None
) -> pd.DataFrame:
    """Aggregiert alle Methoden auf ``(site, date, segment)``.

    Punkt-Methoden werden **hoch**-aggregiert (flag = irgendein Flag im Segment-Tag,
    score = max |score|). Segment-Methoden sind bereits auf dieser Granularität.
    Stunden außerhalb aller Segmente (22–24) fallen heraus.
    """
    cfg = _load_config(config_path)
    seg_defs = cfg["clustering"]["segmente"]["segments"]
    ts = pd.to_datetime(scores["timestamp"])
    hour = ts.dt.hour
    seg = pd.Series(pd.NA, index=scores.index, dtype="object")
    for s in seg_defs:
        seg[(hour >= s["start_hour"]) & (hour < s["end_hour"])] = s["name"]
    grid = scores.assign(date=ts.dt.date, _seg=seg)
    # native segment_day: eigenes Segment verwenden; point: aus der Stunde abgeleitet
    grid["segment_eff"] = grid["segment"].where(grid["granularity"] == "segment_day", grid["_seg"])
    grid = grid.dropna(subset=["segment_eff"])
    agg = grid.groupby(["site", "date", "segment_eff", "method"]).agg(
        flag=("flag", "any"), score=("score", lambda x: x.abs().max())
    )
    return agg.reset_index().rename(columns={"segment_eff": "segment"})


def pairwise_overlap(grid: pd.DataFrame) -> pd.DataFrame:
    """Informelle paarweise Übereinstimmung der Flags je Methodenpaar (Jaccard + Cohen's Kappa)
    auf der Segment-Tag-Ebene."""
    wide = grid.pivot_table(
        index=["site", "date", "segment"], columns="method", values="flag", aggfunc="any"
    ).fillna(False)
    methods = list(wide.columns)
    rows = []
    for i, a in enumerate(methods):
        for b in methods[i + 1 :]:
            fa, fb = wide[a].to_numpy(), wide[b].to_numpy()
            both = int((fa & fb).sum())
            either = int((fa | fb).sum())
            jaccard = both / either if either else float("nan")
            # Cohen's Kappa
            n = len(fa)
            po = float((fa == fb).mean())
            pe = (fa.mean() * fb.mean()) + ((1 - fa.mean()) * (1 - fb.mean()))
            kappa = (po - pe) / (1 - pe) if (1 - pe) else float("nan")
            rows.append({"method_a": a, "method_b": b, "jaccard": jaccard, "kappa": kappa, "n": n})
    return pd.DataFrame(rows)
