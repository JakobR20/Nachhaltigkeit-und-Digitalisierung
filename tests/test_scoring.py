"""Tests für das gemeinsame Score-Format und die Hoch-Aggregation auf Segment-Tag."""
from __future__ import annotations

import pandas as pd

from rausch_energy_anomaly.evaluation.scoring import (
    _SCHEMA,
    pairwise_overlap,
    to_segment_day_grid,
)


def _scores() -> pd.DataFrame:
    def ts(s):
        return pd.Timestamp(s, tz="Europe/Berlin")

    rows = [
        # Punkt-Methode: ein Flag im Nachmittag (14-22) -> Segment-Tag soll True werden
        ("A", ts("2024-06-03 15:00"), "zscore_stl", 4.0, True, "point", pd.NA),
        ("A", ts("2024-06-03 15:15"), "zscore_stl", 1.0, False, "point", pd.NA),
        ("A", ts("2024-06-03 03:00"), "zscore_stl", 2.0, False, "point", pd.NA),
        ("A", ts("2024-06-03 23:00"), "zscore_stl", 9.0, True, "point", pd.NA),  # außerhalb -> raus
        # native Segment-Tag-Methode
        ("A", ts("2024-06-03 14:00"), "cluster_segment", 5.0, True, "segment_day", "nachmittag"),
    ]
    return pd.DataFrame(rows, columns=_SCHEMA)


def test_schema_columns():
    assert _SCHEMA == ["site", "timestamp", "method", "score", "flag", "granularity", "segment"]


def test_point_method_aggregated_up_not_broadcast():
    grid = to_segment_day_grid(_scores())
    assert list(grid.columns) == ["site", "date", "segment", "method", "flag", "score"]
    row = grid[(grid["method"] == "zscore_stl") & (grid["segment"] == "nachmittag")]
    # genau EINE Zeile pro (site, date, segment, method) – kein 96-fach-Broadcast
    assert len(row) == 1
    assert bool(row["flag"].iloc[0]) is True          # any-Flag
    assert row["score"].iloc[0] == 4.0                # max |score|


def test_hours_outside_segments_dropped():
    grid = to_segment_day_grid(_scores())
    # 23:00 liegt in keinem Segment -> der 9.0-Punkt darf nirgends auftauchen
    assert (grid["score"] == 9.0).sum() == 0


def test_segment_day_method_native():
    grid = to_segment_day_grid(_scores())
    row = grid[(grid["method"] == "cluster_segment") & (grid["segment"] == "nachmittag")]
    assert len(row) == 1
    assert row["score"].iloc[0] == 5.0


def test_pairwise_overlap_runs_on_segment_day_grid():
    grid = to_segment_day_grid(_scores())
    ov = pairwise_overlap(grid)
    assert {"method_a", "method_b", "jaccard", "kappa", "n"} <= set(ov.columns)
    # beide Methoden flaggen denselben Nachmittag -> Jaccard = 1 für dieses eine Segment-Tag
    pair = ov.iloc[0]
    assert pair["jaccard"] == 1.0
