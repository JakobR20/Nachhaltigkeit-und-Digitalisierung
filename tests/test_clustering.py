"""Tests für Peer-Gruppen- und distanzbasiertes Segment-Clustering."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rausch_energy_anomaly.models.clustering_daily import DailyProfileClusterer
from rausch_energy_anomaly.models.clustering_segments import SegmentClusterer

FEATURES = ["mean", "max", "std", "slope"]
SEGMENTS = ["nachts"]
K = {"nachts": 2}


# --------------------------------------------------------------------------- #
# DailyProfileClusterer (Peer-Gruppen)
# --------------------------------------------------------------------------- #
def _profiles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1, 2, 3, 4],
            [1, 2, 3, 4.1],
            [1, 2, 3, 3.9],  # Gruppe A: steigend
            [4, 3, 2, 1],
            [4.1, 3, 2, 1],
            [3.9, 3, 2, 1],  # Gruppe B: fallend
        ],
        index=["s1", "s2", "s3", "s4", "s5", "s6"],
    )


def test_daily_peer_groups_separate_shapes_and_deterministic():
    c = DailyProfileClusterer(k=2, seed=0).fit(_profiles())
    lab = c.labels_
    assert lab["s1"] == lab["s2"] == lab["s3"]
    assert lab["s4"] == lab["s5"] == lab["s6"]
    assert lab["s1"] != lab["s4"]
    # predict reproduziert die fit-Labels
    assert (c.predict(_profiles()) == lab).all()
    # deterministisch über zwei Fits
    c2 = DailyProfileClusterer(k=2, seed=0).fit(_profiles())
    assert (c2.labels_ == lab).all()


def test_daily_predict_before_fit_raises():
    with pytest.raises(RuntimeError):
        DailyProfileClusterer().predict(_profiles())


# --------------------------------------------------------------------------- #
# SegmentClusterer (Distanz-Diagnose)
# --------------------------------------------------------------------------- #
def _features() -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(0)
    n = 60
    train = pd.DataFrame(
        {
            "nachts_mean": 5 + rng.normal(0, 0.3, n),
            "nachts_max": 7 + rng.normal(0, 0.3, n),
            "nachts_std": 1 + rng.normal(0, 0.1, n),
            "nachts_slope": rng.normal(0, 0.1, n),
            "nachts_incomplete": [False] * n,
        }
    )
    # extremer ABER incompleter Train-Punkt -> muss aus dem Fit fallen
    extreme_incomplete = pd.DataFrame(
        {
            "nachts_mean": [99.0],
            "nachts_max": [99.0],
            "nachts_std": [99.0],
            "nachts_slope": [99.0],
            "nachts_incomplete": [True],
        }
    )
    # Score-only-Zeilen (kein Train): ein Inlier, ein klarer Ausreißer
    score_rows = pd.DataFrame(
        {
            "nachts_mean": [5.0, 50.0],
            "nachts_max": [7.0, 60.0],
            "nachts_std": [1.0, 20.0],
            "nachts_slope": [0.0, 10.0],
            "nachts_incomplete": [False, False],
        }
    )
    feat = pd.concat([train, extreme_incomplete, score_rows], ignore_index=True)
    train_mask = pd.Series([True] * (n + 1) + [False, False], index=feat.index)
    return feat, train_mask


def test_segment_distance_flags_outlier_not_inlier():
    feat, train_mask = _features()
    sc = SegmentClusterer(SEGMENTS, FEATURES, K, threshold_percentile=99.0, seed=0).fit(
        feat, train_mask
    )
    pred = sc.predict(feat)
    inlier_idx, outlier_idx = feat.index[-2], feat.index[-1]
    assert bool(pred.loc[outlier_idx, "nachts_anomaly"]) is True
    assert bool(pred.loc[inlier_idx, "nachts_anomaly"]) is False
    # Score ist kontinuierlich: Ausreißer-Distanz >> Inlier-Distanz
    sco = sc.score(feat)
    assert sco.loc[outlier_idx, "nachts_distance"] > sco.loc[inlier_idx, "nachts_distance"]


def test_segment_incomplete_excluded_from_fit():
    feat, train_mask = _features()
    sc = SegmentClusterer(SEGMENTS, FEATURES, K, seed=0).fit(feat, train_mask)
    # Scaler-Mittel ~5 beweist, dass der extreme incomplete-Punkt (99) NICHT einging
    assert sc.scalers_["nachts"].mean_[0] == pytest.approx(5.0, abs=0.5)


def test_segment_threshold_from_train_only_and_deterministic():
    feat, train_mask = _features()
    sc1 = SegmentClusterer(SEGMENTS, FEATURES, K, seed=0).fit(feat, train_mask)
    sc2 = SegmentClusterer(SEGMENTS, FEATURES, K, seed=0).fit(feat, train_mask)
    assert sc1.thresholds_["nachts"] == pytest.approx(sc2.thresholds_["nachts"])
    # Schwelle aus eng gestreuten Train-Inliern -> klein (Ausreißer war nicht im Train)
    assert sc1.thresholds_["nachts"] < 5.0


def test_segment_predict_before_fit_raises():
    feat, _ = _features()
    with pytest.raises(RuntimeError):
        SegmentClusterer(SEGMENTS, FEATURES, K).predict(feat)


def test_segment_save_load_roundtrip(tmp_path):
    feat, train_mask = _features()
    sc = SegmentClusterer(SEGMENTS, FEATURES, K, seed=0).fit(feat, train_mask)
    p = tmp_path / "seg.joblib"
    sc.save(p)
    loaded = SegmentClusterer.load(p)
    pd.testing.assert_frame_equal(loaded.predict(feat), sc.predict(feat))
