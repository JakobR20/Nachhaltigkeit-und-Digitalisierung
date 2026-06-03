"""API smoke-tests (FastAPI TestClient). Run: .venv/bin/python -m pytest backend/tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# make `app` importable (backend/ is the app-dir)
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(app)


def test_list_returns_all_66():
    r = client.get("/api/anomalies")
    assert r.status_code == 200
    assert len(r.json()) == 66


def test_filter_by_site():
    r = client.get("/api/anomalies", params={"site": "Baumarkt_06"})
    assert r.status_code == 200
    data = r.json()
    assert data and all(i["site"] == "Baumarkt_06" for i in data)


def test_filter_by_date_range():
    r = client.get("/api/anomalies",
                   params={"date_from": "2024-01-01", "date_to": "2024-12-31"})
    assert r.status_code == 200
    for i in r.json():
        assert "2024" in i["timestamp"][:4]


def test_min_cost_filter():
    r = client.get("/api/anomalies", params={"min_cost": 20})
    assert r.status_code == 200
    assert all((i["mehrkosten_eur"] or 0) >= 20 for i in r.json())


def test_detail_has_load_curve():
    r = client.get("/api/anomalies/21")
    assert r.status_code == 200
    d = r.json()
    assert d["nr"] == "21"
    assert len(d["load_curve"]) > 100  # ±3 days of 15-min points
    assert d["cost"]["jahreskosten_eur"] is not None


def test_ensemble_stats_four_methods():
    r = client.get("/api/ensemble-stats")
    assert r.status_code == 200
    d = r.json()
    assert len(d["methods"]) == 4
    assert all(m["count"] > 0 for m in d["methods"])
    assert d["kappa"]  # non-empty


def test_negative_price_edge_case_nr58():
    r = client.get("/api/anomalies/58")
    assert r.status_code == 200
    d = r.json()
    assert d["cost"]["is_negative_price"] is True


def test_unknown_nr_404():
    assert client.get("/api/anomalies/9999").status_code == 404


@pytest.mark.parametrize("sort_by", ["cost", "date", "severity"])
def test_sort_modes(sort_by):
    r = client.get("/api/anomalies", params={"sort_by": sort_by})
    assert r.status_code == 200
    assert len(r.json()) == 66
