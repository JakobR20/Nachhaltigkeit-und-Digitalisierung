"""Tests für method_comparison gegen ein echtes Mini-Subset von anomaly_scores.parquet.

Der ``mini_scores``-Fixture liest das echte Parquet (lokal vorhanden, gitignored)
und filtert auf 2 Sites × Januar 2024. Wenn das Parquet fehlt (CI ohne Daten),
werden Tests sauber übersprungen.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from rausch_energy_anomaly.evaluation.method_comparison import (
    _AGG_SCHEMA,
    aggregate_to_segment_day,
    compare_at_thresholds,
    precision_from_annotation,
    recommend_strategy,
    summary_table,
)

_SCORES = Path(__file__).resolve().parents[1] / "data" / "processed" / "anomaly_scores.parquet"


@pytest.fixture(scope="session")
def mini_scores() -> pd.DataFrame:
    """2 Sites × Januar 2024 aus dem echten Parquet (gitignored)."""
    if not _SCORES.exists():
        pytest.skip(f"anomaly_scores.parquet nicht vorhanden: {_SCORES}")
    df = pd.read_parquet(_SCORES)
    df = df[df["site"].isin(["Baumarkt_03", "Baumarkt_05"])]
    ts = pd.to_datetime(df["timestamp"])
    start = pd.Timestamp("2024-01-01", tz="Europe/Berlin")
    end = pd.Timestamp("2024-02-01", tz="Europe/Berlin")
    return df[(ts >= start) & (ts < end)].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# aggregate_to_segment_day
# --------------------------------------------------------------------------- #
def test_aggregate_schema(mini_scores):
    out = aggregate_to_segment_day(mini_scores, threshold_pct=0.25)
    assert list(out.columns) == _AGG_SCHEMA
    assert out["flag"].dtype == bool


def test_aggregate_threshold_zero_is_any(mini_scores):
    """threshold_pct=0 reproduziert flag.any() (= alter "any"-Pfad)."""
    out_zero = aggregate_to_segment_day(mini_scores, threshold_pct=0)
    # Manuelle "any"-Aggregation für zscore_stl — gleicher Pre-Filter wie in der Funktion
    # (NaN-Scores raus, Baumarkt_23 raus, bool-Cast).
    sub = mini_scores[
        (mini_scores["method"] == "zscore_stl") & (mini_scores["granularity"] == "point")
    ].copy()
    sub = sub[~sub["site"].isin(("Baumarkt_23",))]
    sub = sub[sub["score"].notna()].copy()
    sub["flag"] = sub["flag"].astype(bool)
    ts = pd.to_datetime(sub["timestamp"])
    sub["date"] = ts.dt.date
    sub["hour"] = ts.dt.hour
    # Segmente aus der Konfig replizieren (vier feste Namen)
    seg_map = {
        "nachts": (0, 6),
        "vormittag": (6, 11),
        "mittag": (11, 14),
        "nachmittag": (14, 22),
    }
    seg = pd.Series(pd.NA, index=sub.index, dtype="object")
    for name, (start, end) in seg_map.items():
        seg = seg.where(~((sub["hour"] >= start) & (sub["hour"] < end)), name)
    sub["segment"] = seg
    sub = sub.dropna(subset=["segment"])
    expected = sub.groupby(["site", "date", "segment"])["flag"].any().rename("flag_expected")

    got = out_zero[out_zero["method"] == "zscore_stl"].set_index(["site", "date", "segment"])[
        "flag"
    ]
    joined = expected.to_frame().join(got.rename("flag_got"), how="inner")
    assert (joined["flag_expected"] == joined["flag_got"]).all(), (
        "threshold_pct=0 muss exakt flag.any() reproduzieren"
    )


def test_aggregate_threshold_one_is_monotone(mini_scores):
    """Bei threshold_pct=1 wird höchstens so viel geflaggt wie bei threshold_pct=0."""
    out_zero = aggregate_to_segment_day(mini_scores, threshold_pct=0)
    out_one = aggregate_to_segment_day(mini_scores, threshold_pct=1.0)
    n_zero = out_zero[out_zero["method"] == "zscore_stl"]["flag"].sum()
    n_one = out_one[out_one["method"] == "zscore_stl"]["flag"].sum()
    assert n_one <= n_zero, "monoton fallend in threshold_pct"


def test_aggregate_drops_out_of_segment_hours(mini_scores):
    """Stunden 22..24 dürfen nicht in die Aggregation einfließen."""
    out = aggregate_to_segment_day(mini_scores, threshold_pct=0.25)
    assert set(out["segment"].unique()) <= {"nachts", "vormittag", "mittag", "nachmittag"}


def test_aggregate_cluster_segment_passthrough(mini_scores):
    out = aggregate_to_segment_day(mini_scores, threshold_pct=0.25)
    cluster_rows = out[out["method"] == "cluster_segment"]
    assert len(cluster_rows) > 0
    assert (cluster_rows["score"] >= 0).all(), "Distanzen sind nicht-negativ"


def test_aggregate_invalid_threshold_raises(mini_scores):
    with pytest.raises(ValueError):
        aggregate_to_segment_day(mini_scores, threshold_pct=-0.1)
    with pytest.raises(ValueError):
        aggregate_to_segment_day(mini_scores, threshold_pct=1.5)


def test_aggregate_excludes_baumarkt_23():
    """EXCLUDE_SITES = ("Baumarkt_23",) wird konsistent gefiltert."""
    fake = pd.DataFrame(
        {
            "site": ["Baumarkt_23", "Baumarkt_03"],
            "timestamp": pd.to_datetime(["2024-01-15 10:00", "2024-01-15 10:00"]).tz_localize(
                "Europe/Berlin"
            ),
            "method": ["zscore_stl", "zscore_stl"],
            "score": [5.0, 5.0],
            "flag": [True, True],
            "granularity": ["point", "point"],
            "segment": [pd.NA, pd.NA],
        }
    )
    out = aggregate_to_segment_day(fake, threshold_pct=0.0)
    assert "Baumarkt_23" not in set(out["site"].unique())


# --------------------------------------------------------------------------- #
# compare_at_thresholds
# --------------------------------------------------------------------------- #
def test_compare_at_thresholds_long_format(mini_scores):
    flag_rates, pairwise = compare_at_thresholds(mini_scores, thresholds=(0.10, 0.25))
    assert {"threshold_pct", "method", "flag_rate_train", "flag_rate_test"} <= set(
        flag_rates.columns
    )
    assert {"threshold_pct", "method_a", "method_b", "jaccard", "kappa"} <= set(pairwise.columns)
    assert set(flag_rates["threshold_pct"].unique()) == {0.10, 0.25}
    assert set(pairwise["threshold_pct"].unique()) == {0.10, 0.25}


# --------------------------------------------------------------------------- #
# precision_from_annotation
# --------------------------------------------------------------------------- #
def test_precision_empty_when_file_missing(tmp_path):
    out = precision_from_annotation(tmp_path / "does_not_exist.csv")
    assert list(out.columns) == ["method", "n_labeled", "tp", "fp", "unklar", "precision"]
    assert len(out) == 0


def test_precision_empty_when_no_labels(tmp_path):
    """Die committed annotation.csv hat leere label-Spalten → leeres Ergebnis."""
    csv = tmp_path / "annotation.csv"
    pd.DataFrame({"method": ["zscore_stl", "arima"], "label": ["", ""], "notiz": ["", ""]}).to_csv(
        csv, index=False
    )
    out = precision_from_annotation(csv)
    assert len(out) == 0


def test_precision_strict_mapping(tmp_path):
    """plausibel_anomal → TP, erklärbar → FP, unklar → exclude."""
    csv = tmp_path / "annotation.csv"
    pd.DataFrame(
        {
            "method": [
                "zscore_stl",
                "zscore_stl",
                "zscore_stl",
                "zscore_stl",
                "zscore_stl",
                "arima",
                "arima",
                "arima",
            ],
            "label": [
                "plausibel_anomal",
                "plausibel_anomal",
                "erklärbar",
                "unklar",
                "",
                "erklärbar",
                "erklärbar",
                "plausibel_anomal",
            ],
        }
    ).to_csv(csv, index=False)
    out = precision_from_annotation(csv)
    z = out[out["method"] == "zscore_stl"].iloc[0]
    assert int(z["tp"]) == 2
    assert int(z["fp"]) == 1
    assert int(z["unklar"]) == 1
    assert abs(float(z["precision"]) - 2 / 3) < 1e-9
    a = out[out["method"] == "arima"].iloc[0]
    assert int(a["tp"]) == 1
    assert int(a["fp"]) == 2
    assert abs(float(a["precision"]) - 1 / 3) < 1e-9


# --------------------------------------------------------------------------- #
# recommend_strategy
# --------------------------------------------------------------------------- #
def _fake_pairwise(kappas: dict[tuple[str, str], float], x: float = 0.25) -> pd.DataFrame:
    rows = []
    for (a, b), k in kappas.items():
        rows.append(
            {
                "threshold_pct": x,
                "method_a": a,
                "method_b": b,
                "jaccard": 0.0,
                "kappa": k,
                "n": 100,
            }
        )
    return pd.DataFrame(rows)


def test_recommend_empty_precision():
    pairwise = _fake_pairwise(
        {
            ("zscore_stl", "arima"): 0.5,
            ("zscore_stl", "cluster_segment"): 0.1,
            ("arima", "cluster_segment"): 0.1,
        }
    )
    empty = pd.DataFrame(columns=["method", "n_labeled", "tp", "fp", "unklar", "precision"])
    strategy, label, rationale = recommend_strategy(empty, pairwise, x_default=0.25)
    assert strategy == "ensemble"
    assert label == "to_be_chosen_after_annotation"


def test_recommend_single_winner_when_only_one_qualifies():
    """Nur zscore_stl erfüllt precision ≥ 0,90 UND max κ ≤ 0,40 → single."""
    precision = pd.DataFrame(
        {
            "method": ["zscore_stl", "arima", "cluster_segment"],
            "n_labeled": [10, 10, 10],
            "tp": [9, 4, 4],
            "fp": [1, 6, 6],
            "unklar": [0, 0, 0],
            "precision": [0.90, 0.40, 0.40],
        }
    )
    pairwise = _fake_pairwise(
        {
            ("zscore_stl", "arima"): 0.30,
            ("zscore_stl", "cluster_segment"): 0.10,
            ("arima", "cluster_segment"): 0.20,
        }
    )
    strategy, label, _ = recommend_strategy(precision, pairwise, x_default=0.25)
    assert strategy == "single"
    assert label == "zscore_stl"


def test_recommend_ensemble_when_kappa_too_high():
    """Auch wenn precision ≥ 0,90 — κ > 0,40 vs irgendeiner anderen disqualifiziert."""
    precision = pd.DataFrame(
        {
            "method": ["zscore_stl", "arima", "cluster_segment"],
            "n_labeled": [10, 10, 10],
            "tp": [9, 4, 4],
            "fp": [1, 6, 6],
            "unklar": [0, 0, 0],
            "precision": [0.90, 0.40, 0.40],
        }
    )
    pairwise = _fake_pairwise(
        {
            ("zscore_stl", "arima"): 0.50,  # > 0,40
            ("zscore_stl", "cluster_segment"): 0.10,
            ("arima", "cluster_segment"): 0.20,
        }
    )
    strategy, label, _ = recommend_strategy(precision, pairwise, x_default=0.25)
    assert strategy == "ensemble"
    assert label == "union_or_voting"


def test_recommend_ensemble_when_precisions_all_below_threshold():
    """Keine Methode erreicht precision ≥ 0,90 → ensemble (union_or_voting)."""
    precision = pd.DataFrame(
        {
            "method": ["zscore_stl", "arima", "cluster_segment"],
            "n_labeled": [10, 10, 10],
            "tp": [8, 7, 4],
            "fp": [2, 3, 6],
            "unklar": [0, 0, 0],
            "precision": [0.80, 0.70, 0.40],
        }
    )
    pairwise = _fake_pairwise(
        {
            ("zscore_stl", "arima"): 0.30,
            ("zscore_stl", "cluster_segment"): 0.10,
            ("arima", "cluster_segment"): 0.20,
        }
    )
    strategy, label, _ = recommend_strategy(precision, pairwise, x_default=0.25)
    assert strategy == "ensemble"
    assert label == "union_or_voting"


def test_recommend_ensemble_union_when_multiple_qualify():
    """Plausibilitäts-Annotation-Szenario: alle drei precision ≥ 0,90 UND κ alle ≤ 0,40
    → ensemble (union), weil Komplementarität disjunkte Anomalie-Mengen beweist."""
    precision = pd.DataFrame(
        {
            "method": ["zscore_stl", "arima", "cluster_segment"],
            "n_labeled": [20, 17, 20],
            "tp": [20, 17, 20],
            "fp": [0, 0, 0],
            "unklar": [0, 0, 0],
            "precision": [1.00, 1.00, 1.00],
        }
    )
    pairwise = _fake_pairwise(
        {
            ("zscore_stl", "arima"): 0.0,
            ("zscore_stl", "cluster_segment"): 0.0,
            ("arima", "cluster_segment"): 0.0,
        }
    )
    strategy, label, rationale = recommend_strategy(precision, pairwise, x_default=0.25)
    assert strategy == "ensemble"
    assert label == "union"
    assert "disjunkt" in rationale.lower() or "komplementär" in rationale.lower()


# --------------------------------------------------------------------------- #
# summary_table
# --------------------------------------------------------------------------- #
def test_summary_table_contains_methods(mini_scores):
    flag_rates, pairwise = compare_at_thresholds(mini_scores, thresholds=(0.25,))
    md = summary_table(flag_rates, pairwise, x_default=0.25)
    for m in ("zscore_stl", "arima", "cluster_segment"):
        assert m in md
    assert "| Methode |" in md


def test_summary_table_precision_dash_when_empty(mini_scores):
    flag_rates, pairwise = compare_at_thresholds(mini_scores, thresholds=(0.25,))
    md = summary_table(flag_rates, pairwise, x_default=0.25, precision_df=pd.DataFrame())
    # Precision-Spalte mit Dash, wenn Annotation noch leer
    assert "Precision" in md
