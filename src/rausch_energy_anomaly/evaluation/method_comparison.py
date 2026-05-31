"""Methodenvergleich (Schritt 11) für die drei portierten Methoden.

Funktionen:

- :func:`aggregate_to_segment_day` — Punkt-Methoden auf ``(site, date, segment)``
  mit Anteils-Schwelle aggregieren (ersetzt das ``any`` aus
  :func:`rausch_energy_anomaly.evaluation.scoring.to_segment_day_grid`).
- :func:`compare_at_thresholds` — X-Sweep, Flag-Raten + paarweise κ/Jaccard.
- :func:`precision_from_annotation` — Precision je Methode aus
  ``reports/annotation/annotation.csv`` (siehe Funktions-Doku zum Mapping).
- :func:`recommend_strategy` — Sieger- oder Ensemble-Empfehlung über absolute
  Schwellen: precision ≥ 0,90 UND max κ vs jede andere Methode ≤ 0,40
  (mehrere Erfüller → Ensemble Union, weil κ ≤ 0,40 Komplementarität beweist).
- :func:`inference_timing` — Wall-Time fit + score je Methode auf festem
  Sites-Subset (Loader-Lauf einmal).
- :func:`summary_table` — Markdown-Vergleichstabelle.
- :func:`load_default_threshold_pct` — gewähltes ``threshold_pct`` aus
  ``config/config.yaml`` (``comparison.aggregation_threshold_pct``); ``None``
  solange nicht gesetzt.

Designnotiz: Wahl von ``X`` ist eine methodische Entscheidung nach dem
X-Sweep im Notebook (Cluster-Distanz als Anker) — wird *einmal* gewählt
und in der Config + methodology.md festgeschrieben.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd

from rausch_energy_anomaly.evaluation.scoring import _load_config

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ANNOTATION = _ROOT / "reports" / "annotation" / "annotation.csv"

EXCLUDE_SITES: tuple[str, ...] = ("Baumarkt_23",)
DEFAULT_THRESHOLDS: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75)
DEFAULT_TRAIN_END = pd.Timestamp("2024-12-31").date()

_AGG_SCHEMA = ["site", "date", "segment", "method", "flag", "score"]

_NATIVE_GRANULARITY = {
    "zscore_stl": "point (15 min)",
    "arima": "point (15 min)",
    "cluster_segment": "segment_day",
    "autoencoder": "point (15 min)",
}
_STRENGTH = {
    "zscore_stl": "Punkt-Outlier auf STL-Residual; transparent, schnell",
    "arima": "Lokal-prognostische Abweichung, Peer-Gruppen-Sensitivität",
    "cluster_segment": "Form-/Segment-untypisch; methoden-agnostische Diagnose",
    "autoencoder": "Form-/Niveau-Abweichung im 24h-Lastgang; pro-Site-normiert, deep",
}
_WEAKNESS = {
    "zscore_stl": "Schwellwert manuell, Niveau-Drift schlecht erfasst",
    "arima": "Sensitiv gegen Train-Bias, langsamer",
    "cluster_segment": "Keine 15-min-Lokalisierung im Segment",
    "autoencoder": "DST-/Teiltage werden NaN; Zwischen-Site-Magnitude wegnormiert",
}


def load_default_threshold_pct(config_path: str | Path | None = None) -> float | None:
    """Liest ``cfg['comparison']['aggregation_threshold_pct']``; ``None`` wenn fehlt."""
    cfg = _load_config(config_path)
    return cfg.get("comparison", {}).get("aggregation_threshold_pct")


# --------------------------------------------------------------------------- #
# Aggregation auf (site, date, segment) mit Anteils-Schwelle
# --------------------------------------------------------------------------- #
def aggregate_to_segment_day(
    scores: pd.DataFrame, threshold_pct: float, config_path: str | Path | None = None
) -> pd.DataFrame:
    """Punkt-Methoden auf Segment-Tag mit ``≥ threshold_pct``-Anteilsschwelle aggregieren.

    Für ``granularity == "point"`` und jedes ``(site, date, segment, method)``:

    - ``threshold_pct == 0``: ``flag := flag.any()`` (= "irgendein Flag im
      Segment", reproduziert das alte ``to_segment_day_grid``).
    - ``threshold_pct > 0``: ``flag := (flag.sum() / count) ≥ threshold_pct``.
    - ``score := max(|score|)`` über das Segment.

    Stunden außerhalb der konfigurierten Segmente (typisch 22–24) fallen
    heraus. ``cluster_segment`` (``granularity == "segment_day"``) wird
    1:1 durchgereicht. ``EXCLUDE_SITES`` (Baumarkt_23) wird konsistent zu
    ``export_annotation`` herausgefiltert.
    """
    if not 0 <= threshold_pct <= 1:
        raise ValueError(f"threshold_pct muss in [0, 1] liegen, nicht {threshold_pct}")

    cfg = _load_config(config_path)
    seg_defs = cfg["clustering"]["segmente"]["segments"]
    seg_ranges = {s["name"]: (s["start_hour"], s["end_hour"]) for s in seg_defs}

    scores = scores[~scores["site"].isin(EXCLUDE_SITES)]
    scores = scores[scores["score"].notna()].copy()
    scores["flag"] = scores["flag"].astype(bool)

    ts = pd.to_datetime(scores["timestamp"])
    scores["date"] = ts.dt.date
    hour = ts.dt.hour

    is_point = scores["granularity"] == "point"
    seg_from_hour = pd.Series(pd.NA, index=scores.index, dtype="object")
    for name, (start, end) in seg_ranges.items():
        seg_from_hour = seg_from_hour.where(~((hour >= start) & (hour < end)), name)

    point = scores[is_point].assign(segment_eff=seg_from_hour[is_point])
    point = point.dropna(subset=["segment_eff"])

    grp = point.groupby(["site", "date", "segment_eff", "method"], observed=True).agg(
        flag_sum=("flag", "sum"),
        flag_count=("flag", "count"),
        score=("score", lambda s: s.abs().max()),
    )
    if threshold_pct == 0:
        grp["flag"] = grp["flag_sum"] >= 1
    else:
        grp["flag"] = (grp["flag_sum"] / grp["flag_count"]) >= threshold_pct
    point_out = (
        grp.drop(columns=["flag_sum", "flag_count"])
        .reset_index()
        .rename(columns={"segment_eff": "segment"})
    )

    seg_native = scores[scores["granularity"] == "segment_day"].copy()
    seg_native["score"] = seg_native["score"].abs()
    seg_native = seg_native[["site", "date", "segment", "method", "flag", "score"]]

    out = pd.concat([point_out, seg_native], ignore_index=True)
    return out[_AGG_SCHEMA]


# --------------------------------------------------------------------------- #
# X-Sweep: Flag-Raten und paarweise Übereinstimmung
# --------------------------------------------------------------------------- #
def _pairwise_overlap(grid: pd.DataFrame) -> pd.DataFrame:
    """Paarweise Jaccard + Cohen's κ zwischen allen Methoden auf gemeinsamer Grid."""
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
            pa, pb = float(fa.mean()), float(fb.mean())
            po = float((fa == fb).mean())
            pe = pa * pb + (1 - pa) * (1 - pb)
            kappa = (po - pe) / (1 - pe) if (1 - pe) else float("nan")
            rows.append(
                {"method_a": a, "method_b": b, "jaccard": jaccard, "kappa": kappa, "n": len(fa)}
            )
    return pd.DataFrame(rows)


def compare_at_thresholds(
    scores: pd.DataFrame,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    train_end_date=None,
    config_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """X-Sweep: pro ``threshold_pct`` Flag-Raten je Methode + paarweise κ/Jaccard.

    Returns ``(flag_rates, pairwise)``:

    - ``flag_rates``: ``threshold_pct, method, flag_rate_train, flag_rate_test, n_train, n_test``
    - ``pairwise``:   ``threshold_pct, method_a, method_b, jaccard, kappa, n``
    """
    if train_end_date is None:
        train_end_date = DEFAULT_TRAIN_END

    flag_rows: list[dict] = []
    pair_frames: list[pd.DataFrame] = []
    for x in thresholds:
        grid = aggregate_to_segment_day(scores, threshold_pct=x, config_path=config_path)
        is_train = grid["date"].apply(lambda d: d <= train_end_date)
        for method, mdf in grid.groupby("method", observed=True):
            tr_mask = is_train.loc[mdf.index]
            tr_rate = float(mdf.loc[tr_mask, "flag"].mean()) if tr_mask.any() else float("nan")
            te_rate = float(mdf.loc[~tr_mask, "flag"].mean()) if (~tr_mask).any() else float("nan")
            flag_rows.append(
                {
                    "threshold_pct": x,
                    "method": method,
                    "flag_rate_train": tr_rate,
                    "flag_rate_test": te_rate,
                    "n_train": int(tr_mask.sum()),
                    "n_test": int((~tr_mask).sum()),
                }
            )
        pw = _pairwise_overlap(grid)
        pw.insert(0, "threshold_pct", x)
        pair_frames.append(pw)

    pairwise = pd.concat(pair_frames, ignore_index=True) if pair_frames else pd.DataFrame()
    return pd.DataFrame(flag_rows), pairwise


# --------------------------------------------------------------------------- #
# Precision aus Annotation
# --------------------------------------------------------------------------- #
def precision_from_annotation(
    annotation_csv_path: str | Path | None = None,
) -> pd.DataFrame:
    """Precision je Methode aus ``annotation.csv`` (Default: ``reports/annotation/``).

    **Label-Mapping (strenge Variante, fürs Paper konsistent):**

    - ``plausibel_anomal`` → **TP**: echte Anomalie, handlungsrelevant.
    - ``erklärbar``        → **FP**: sichtbar, aber NICHT handlungsrelevant
      (Feiertag, Wartung, Inbetriebnahme, Wetterspitze, Inventur).
    - ``unklar``           → **ausgeschlossen** (kein Beitrag zu TP/FP).

    ``erklärbar`` als FP zu zählen ist die strenge Lesart: die Methode hat
    ein erklärbares (= nicht-anomales) Ereignis als Anomalie markiert
    → Fehlalarm im Sinne von „nicht handlungsrelevant". Die andere Lesart
    („TP wenn der Score korrekt hoch lag") ist wahrnehmungs- statt
    handlungs-zentriert und wurde bewusst nicht gewählt, weil das
    Anwendungskriterium bei Rausch ist, ob aus dem Flag eine Handlung folgt
    (siehe methodology.md, Abschnitt „Precision-Definition").

    Bei fehlender Datei oder leeren ``label``-Spalten: leerer DataFrame mit
    korrekten Spalten + dtypes (Notebook läuft ohne Annotation durch).
    """
    path = Path(annotation_csv_path) if annotation_csv_path is not None else _DEFAULT_ANNOTATION
    empty = pd.DataFrame(
        {
            "method": pd.Series(dtype="object"),
            "n_labeled": pd.Series(dtype="int64"),
            "tp": pd.Series(dtype="int64"),
            "fp": pd.Series(dtype="int64"),
            "unklar": pd.Series(dtype="int64"),
            "precision": pd.Series(dtype="float64"),
        }
    )
    if not path.exists():
        return empty
    df = pd.read_csv(path)
    if "label" not in df.columns or "method" not in df.columns:
        return empty
    df["label"] = df["label"].fillna("").astype(str).str.strip()
    labeled = df[df["label"] != ""]
    if not len(labeled):
        return empty

    def _count(series: pd.Series, value: str) -> int:
        return int((series == value).sum())

    grouped = (
        labeled.groupby("method", observed=True)
        .agg(
            n_labeled=("label", "size"),
            tp=("label", lambda x: _count(x, "plausibel_anomal")),
            fp=("label", lambda x: _count(x, "erklärbar")),
            unklar=("label", lambda x: _count(x, "unklar")),
        )
        .reset_index()
    )
    grouped["precision"] = grouped.apply(
        lambda r: (
            float(r["tp"]) / float(r["tp"] + r["fp"]) if (r["tp"] + r["fp"]) > 0 else float("nan")
        ),
        axis=1,
    )
    return grouped[["method", "n_labeled", "tp", "fp", "unklar", "precision"]]


# --------------------------------------------------------------------------- #
# Empfehlung Sieger-Methode vs Ensemble
# --------------------------------------------------------------------------- #
def recommend_strategy(
    precision_df: pd.DataFrame,
    pairwise_df: pd.DataFrame,
    x_default: float,
) -> tuple[str, str, str]:
    """Sieger-Methode oder Ensemble auf Basis absoluter Precision + Komplementarität.

    **Hintergrund (Felix/Jakob-Annotation, 30.05.2026):** Die Plausibilitäts-
    Stichprobe wählt absichtlich nur die Top-|score|-Kandidaten je Methode
    (siehe ``export_annotation``). Erwartung: die Precision auf dieser
    Stichprobe liegt bei *allen* Methoden hoch — die Differenz zwischen den
    Methoden trennt nicht. Deshalb keine Vorsprungs-Regel, sondern *absolute*
    Schwellen: eine Methode hat erst dann Sieger-Status, wenn sie **beide**
    Kriterien erfüllt:

    1. ``precision ≥ 0,90`` (Mindest-Plausibilität).
    2. ``max(κ vs jede andere Methode) ≤ 0,4`` (deutliche Komplementarität —
       ihre Anomalie-Menge überlappt nicht stark mit den anderen).

    Erfüllt **genau eine** Methode beide → ``single``. Erfüllen **mehrere**
    Methoden beide → ``ensemble (union)`` — denn die geringe paarweise κ
    beweist, dass sie **disjunkte** Anomalie-Mengen finden; ein Ensemble
    summiert komplementäres Wissen statt redundantes. Erfüllt **keine** →
    ``ensemble (union_or_voting)`` als Fallback.

    Ensemble-Varianten:

    - **Union** (sensitiv, niedrige False-Negative-Rate) → Rausch-Dashboard.
    - **Voting / Mehrheit** (konservativ, höhere Precision) → Pflicht-Report.

    Returns ``(strategy, label, rationale)``:

    - ``strategy ∈ {"single", "ensemble"}``
    - ``label``: Methodenname (single) / ``"union"`` (mehrere Erfüller) /
      ``"union_or_voting"`` (kein Erfüller) /
      ``"to_be_chosen_after_annotation"`` (leere Precision).
    - ``rationale``: kurzer Begründungssatz für methodology.md.
    """
    if precision_df.empty or precision_df["precision"].isna().all():
        return (
            "ensemble",
            "to_be_chosen_after_annotation",
            "Annotation noch nicht eingespeist – Sieger-Entscheidung benötigt Precision-Werte.",
        )

    pair_x = pairwise_df[pairwise_df["threshold_pct"] == x_default]
    if pair_x.empty:
        return (
            "ensemble",
            "union_or_voting",
            f"Keine Pairwise-Daten für threshold_pct={x_default} – Ensemble als Default.",
        )

    methods = sorted(precision_df["method"].dropna().unique())
    precisions: dict[str, float] = dict(
        zip(precision_df["method"], precision_df["precision"], strict=False)
    )
    kappa_to: dict[str, list[float]] = {m: [] for m in methods}
    for _, row in pair_x.iterrows():
        if row["method_a"] in kappa_to and not pd.isna(row["kappa"]):
            kappa_to[row["method_a"]].append(float(row["kappa"]))
        if row["method_b"] in kappa_to and not pd.isna(row["kappa"]):
            kappa_to[row["method_b"]].append(float(row["kappa"]))

    qualifiers: list[tuple[str, float, float]] = []
    for m in methods:
        p = precisions.get(m)
        if p is None or pd.isna(p) or float(p) < 0.90:
            continue
        max_k = max(kappa_to[m]) if kappa_to[m] else 0.0
        if max_k > 0.40:
            continue
        qualifiers.append((m, float(p), max_k))

    if len(qualifiers) == 1:
        m, p, mk = qualifiers[0]
        return (
            "single",
            m,
            (f"Sieger: '{m}' (precision={p:.2f} ≥ 0,90 UND max κ vs andere = {mk:.2f} ≤ 0,40)."),
        )

    if len(qualifiers) > 1:
        names = ", ".join(q[0] for q in qualifiers)
        return (
            "ensemble",
            "union",
            (
                f"{len(qualifiers)} Methoden erfüllen das Sieger-Kriterium ({names}); "
                "ihre paarweise κ ≤ 0,40 zeigt, dass sie disjunkte Anomalie-Mengen "
                "detektieren. Union summiert komplementäres Wissen — "
                "Default-Ensemble für das Dashboard."
            ),
        )

    return (
        "ensemble",
        "union_or_voting",
        (
            "Keine Methode erfüllt das Sieger-Kriterium "
            "(precision ≥ 0,90 UND max κ vs andere ≤ 0,40). "
            "Ensemble: Union (sensitiv, Dashboard) oder Voting (konservativ, "
            "Reporting) je nach Use-Case."
        ),
    )


# --------------------------------------------------------------------------- #
# Microbenchmark Inferenzzeit (Notebook-Aufruf, nicht in der Test-Suite)
# --------------------------------------------------------------------------- #
def inference_timing(
    category: str = "Baumärkte",
    sites: list[str] | None = None,
    config_path: str | Path | None = None,
) -> pd.DataFrame:
    """Wall-Time fit + score je Methode auf festem Sites-Subset.

    Loader läuft einmal (~45 s). Default ``sites``: erste 5 soliden Sites
    (``vmax >= 1 kW``), Baumarkt_23 ausgeschlossen.

    Returns ``method, wall_time_fit_s, wall_time_score_s, n_sites``.
    """
    from rausch_energy_anomaly.features.stl_decompose import stl_decompose
    from rausch_energy_anomaly.ingestion import rlm_loader as loader
    from rausch_energy_anomaly.models.arima_clustered import ArimaClusteredDetector
    from rausch_energy_anomaly.models.baseline_zscore import ZScoreDetector
    from rausch_energy_anomaly.models.clustering_daily import DailyProfileClusterer
    from rausch_energy_anomaly.models.clustering_segments import SegmentClusterer

    cfg = _load_config(config_path)
    period = cfg["models"]["zscore"]["stl_period"]
    z_thr = cfg["models"]["zscore"]["threshold"]
    k_daily = cfg["clustering"]["tagesprofile"]["k_final"]
    seg_defs = cfg["clustering"]["segmente"]["segments"]
    seg_names = [s["name"] for s in seg_defs]
    features = cfg["clustering"]["segmente"]["features_per_segment"]
    k_seg = cfg["clustering"]["segmente"]["k_final_per_segment"]
    thr_pct_cluster = cfg["clustering"]["segmente"]["distance_threshold_percentile"]
    train_end = pd.Timestamp("2024-12-31 23:45", tz="Europe/Berlin")

    df = loader.load_category(category)
    vmax = df.groupby(level="meter_id")["value_kw"].max()
    solid = sorted(vmax[vmax >= 1.0].index)
    if sites is None:
        sites = [s for s in solid if s not in EXCLUDE_SITES][:5]

    stl = {s: stl_decompose(df.xs(s, level="meter_id")["value_kw"], period=period) for s in sites}
    rows: list[dict] = []

    # 1) Z-Score
    t0 = time.time()
    z_dets = {s: ZScoreDetector(threshold=z_thr).fit(stl[s]["stl_resid"]) for s in sites}
    z_fit = time.time() - t0
    t0 = time.time()
    for s in sites:
        z_dets[s].score(stl[s]["stl_resid"])
    z_score = time.time() - t0
    rows.append(
        {
            "method": "zscore_stl",
            "wall_time_fit_s": z_fit,
            "wall_time_score_s": z_score,
            "n_sites": len(sites),
        }
    )

    # 2) ARIMA (peer-cluster + group-fit, scoring per site)
    from rausch_energy_anomaly.evaluation.scoring import _site_mean_profile

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

    t0 = time.time()
    arima = ArimaClusteredDetector().fit({g: s.iloc[-20000:] for g, s in repr_by_group.items()})
    a_fit = time.time() - t0
    t0 = time.time()
    for s in sites:
        arima.score(stl[s]["stl_deseasonalized"], group=labels[s], fit_end=train_end)
    a_score = time.time() - t0
    rows.append(
        {
            "method": "arima",
            "wall_time_fit_s": a_fit,
            "wall_time_score_s": a_score,
            "n_sites": len(sites),
        }
    )

    # 3) Cluster-Distanz
    seg = pd.read_parquet(_ROOT / "data" / "processed" / "segment_features.parquet")
    seg = seg.loc[seg.index.get_level_values("site").isin(sites)]
    train_end_date = train_end.date()
    seg_dates_idx = seg.index.get_level_values("date")
    train_mask = pd.Series([d <= train_end_date for d in seg_dates_idx], index=seg.index)

    t0 = time.time()
    sclu = SegmentClusterer(seg_names, features, k_seg, threshold_percentile=thr_pct_cluster).fit(
        seg, train_mask
    )
    c_fit = time.time() - t0
    t0 = time.time()
    sclu.score(seg)
    sclu.predict(seg)
    c_score = time.time() - t0
    rows.append(
        {
            "method": "cluster_segment",
            "wall_time_fit_s": c_fit,
            "wall_time_score_s": c_score,
            "n_sites": len(sites),
        }
    )

    # 4) Autoencoder (Dense, ein Modell über alle Sites; Default-Hyperparameter)
    from rausch_energy_anomaly.models.autoencoder import AutoencoderDetector

    series_by_site_ae = {s: df.xs(s, level="meter_id")["value_kw"] for s in sites}
    t0 = time.time()
    ae = AutoencoderDetector(variant="dense").fit(series_by_site_ae, fit_end=train_end)
    ae_fit = time.time() - t0
    t0 = time.time()
    for s in sites:
        ae.score(series_by_site_ae[s], s)
    ae_score = time.time() - t0
    rows.append(
        {
            "method": "autoencoder",
            "wall_time_fit_s": ae_fit,
            "wall_time_score_s": ae_score,
            "n_sites": len(sites),
        }
    )

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Markdown-Vergleichstabelle
# --------------------------------------------------------------------------- #
def _to_markdown(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def summary_table(
    flag_rates_df: pd.DataFrame,
    pairwise_df: pd.DataFrame,
    x_default: float,
    timing_df: pd.DataFrame | None = None,
    precision_df: pd.DataFrame | None = None,
) -> str:
    """Markdown-Vergleichstabelle bei ``x_default``. Lückenhafte Inputs → ``—``."""
    flags_x = flag_rates_df[flag_rates_df["threshold_pct"] == x_default]
    pair_x = pairwise_df[pairwise_df["threshold_pct"] == x_default]
    methods = sorted(flags_x["method"].unique())

    def _kappas(m: str) -> str:
        ks: dict[str, float] = {}
        for _, p in pair_x.iterrows():
            if p["method_a"] == m:
                ks[p["method_b"]] = p["kappa"]
            elif p["method_b"] == m:
                ks[p["method_a"]] = p["kappa"]
        return ", ".join(f"{o}={v:.2f}" for o, v in sorted(ks.items())) if ks else "—"

    def _timing(m: str) -> tuple[str, str]:
        if timing_df is None or timing_df.empty:
            return "—", "—"
        t = timing_df[timing_df["method"] == m]
        if t.empty:
            return "—", "—"
        return (
            f"{float(t['wall_time_fit_s'].iloc[0]):.2f}",
            f"{float(t['wall_time_score_s'].iloc[0]):.2f}",
        )

    def _precision(m: str) -> str:
        if precision_df is None or precision_df.empty:
            return "—"
        pr = precision_df[precision_df["method"] == m]
        if pr.empty or pd.isna(pr["precision"].iloc[0]):
            return "—"
        return f"{float(pr['precision'].iloc[0]) * 100:.0f}%"

    rows = []
    for m in methods:
        flag_row = flags_x[flags_x["method"] == m].iloc[0]
        wf, ws = _timing(m)
        rows.append(
            {
                "Methode": m,
                "Native Granularität": _NATIVE_GRANULARITY.get(m, "—"),
                "Flag-Rate Train": f"{flag_row['flag_rate_train'] * 100:.2f}%",
                "Flag-Rate Test": f"{flag_row['flag_rate_test'] * 100:.2f}%",
                "κ vs andere": _kappas(m),
                "Wall-Time fit (s)": wf,
                "Wall-Time score (s)": ws,
                "Precision": _precision(m),
                "Stärke": _STRENGTH.get(m, "—"),
                "Schwäche": _WEAKNESS.get(m, "—"),
            }
        )

    return _to_markdown(pd.DataFrame(rows))
