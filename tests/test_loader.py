"""Smoke-Test für den Smart-Meter-Loader.

Prüft, dass die drei Schema-Varianten auf ein identisches Zielschema
normalisieren und dass die meter_id-Vergabe über Mapping stabil bleibt.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pandas as pd
import pytest

from rausch_energy_anomaly.ingestion import rlm_loader as loader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data" / "raw"

BAUMARKT_FILE = RAW / "Baumärkte" / "Zeitreihenvisualisierung_13032026_142924.xlsx"
LASTGANG_FILE = RAW / "Handel" / "Lastgang_34_2023-01-01-2025-12-31.xlsx"

EXPECTED_COLUMNS = ["value_kw", "is_substitute"]
EXPECTED_INDEX_NAMES = ["meter_id", "timestamp"]


def _assert_target_schema(df: pd.DataFrame) -> None:
    assert list(df.index.names) == EXPECTED_INDEX_NAMES
    assert list(df.columns) == EXPECTED_COLUMNS
    assert df["value_kw"].dtype == float
    assert df["is_substitute"].dtype == bool
    ts = df.index.get_level_values("timestamp")
    assert str(ts.tz) == "Europe/Berlin"
    # source_meta_id darf nie im Analyse-DataFrame auftauchen
    assert "source_meta_id" not in df.columns


@pytest.mark.skipif(not BAUMARKT_FILE.exists(), reason="Rohdaten nicht vorhanden")
def test_zrv_and_lastgang_share_schema(capsys):
    """ZRV (kW) und Lastgang (kWh) ergeben dasselbe Zielschema."""
    zrv = loader.load_smartmeter(BAUMARKT_FILE)
    lg = loader.load_smartmeter(LASTGANG_FILE)

    _assert_target_schema(zrv)
    _assert_target_schema(lg)

    # Lastgang hat echte Ersatzwerte, ZRV nie
    assert lg["is_substitute"].any()
    assert not zrv["is_substitute"].any()

    print(f"\nZRV  {zrv.index.get_level_values('meter_id')[0]}: shape={zrv.shape}")
    print(zrv.head(3))
    print(f"\nLastgang {lg.index.get_level_values('meter_id')[0]}: shape={lg.shape}")
    print(lg.head(3))


def _make_temp_category(tmp_path: Path, n: int = 3) -> tuple[Path, Path, list[str]]:
    """Kopiert n Baumarkt-Dateien in eine temporäre Kategorie-Struktur."""
    raw_dir = tmp_path / "raw"
    cat_dir = raw_dir / "Baumärkte"
    cat_dir.mkdir(parents=True)
    src_files = sorted((RAW / "Baumärkte").glob("*.xlsx"))[:n]
    names = []
    for f in src_files:
        shutil.copy(f, cat_dir / f.name)
        names.append(f.name)
    mapping_path = tmp_path / "processed" / "_meter_id_mapping.csv"
    return raw_dir, mapping_path, names


@pytest.mark.skipif(not BAUMARKT_FILE.exists(), reason="Rohdaten nicht vorhanden")
def test_mapping_is_stable(tmp_path, caplog):
    raw_dir, mapping_path, names = _make_temp_category(tmp_path)

    # 1. Erster Aufruf: Mapping entsteht
    df1 = loader.load_category("Baumärkte", raw_dir=raw_dir, mapping_path=mapping_path)
    assert mapping_path.exists()
    _assert_target_schema(df1)
    ids1 = sorted(df1.index.get_level_values("meter_id").unique())
    assert ids1 == ["Baumarkt_01", "Baumarkt_02", "Baumarkt_03"]

    # 2. Zweiter Aufruf: identische IDs, keine Neuvergabe
    with caplog.at_level(logging.INFO):
        df2 = loader.load_category("Baumärkte", raw_dir=raw_dir, mapping_path=mapping_path)
    ids2 = sorted(df2.index.get_level_values("meter_id").unique())
    assert ids2 == ids1
    assert "0 neue meter_id(s) vergeben." in caplog.text

    # 3. Eine Datei künstlich entfernen -> Warnung, kein Crash, IDs stabil
    removed = sorted((raw_dir / "Baumärkte").glob("*.xlsx"))[1]
    removed.unlink()
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        df3 = loader.load_category("Baumärkte", raw_dir=raw_dir, mapping_path=mapping_path)
    assert "Mapping-Lücke" in caplog.text
    ids3 = set(df3.index.get_level_values("meter_id").unique())
    # verbleibende IDs unverändert (Lücke akzeptiert, kein Reindex)
    assert ids3 == set(ids1) - {_id_for(mapping_path, removed.name)}


def _id_for(mapping_path: Path, filename: str) -> str:
    m = pd.read_csv(mapping_path)
    return m.loc[m["filename"] == filename, "meter_id"].iloc[0]


# --------------------------------------------------------------------------- #
# Site-Konfiguration: generischer defaults-Fallback
# --------------------------------------------------------------------------- #
_DEFAULTS_YAML = (
    "defaults:\n"
    "  lat: 49.7913\n"
    "  lon: 9.9534\n"
    "  bundesland: BY\n"
    "  lat_lon_source: default_fallback\n"
)


def test_resolve_site_full_fields_no_fallback(tmp_path, caplog):
    sites = tmp_path / "sites.yaml"
    sites.write_text(
        _DEFAULTS_YAML
        + "sites:\n  - id: site_full\n    lat: 50.1\n    lon: 8.7\n    bundesland: HE\n",
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING):
        site = loader.resolve_site("site_full", path=sites)
    assert (site["lat"], site["lon"], site["bundesland"]) == (50.1, 8.7, "HE")
    assert "default coords" not in caplog.text


def test_resolve_site_null_fields_use_defaults_and_warn(tmp_path, caplog):
    sites = tmp_path / "sites.yaml"
    sites.write_text(
        _DEFAULTS_YAML
        + "sites:\n  - id: site_null\n    lat: null\n    lon: null\n    bundesland: null\n",
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING):
        site = loader.resolve_site("site_null", path=sites)
    assert site["lat"] == 49.7913
    assert site["bundesland"] == "BY"
    assert site["lat_lon_source"] == "default_fallback"
    assert "Using default coords from sites.yaml defaults for site=site_null" in caplog.text
