"""
Loader für die RAUSCH-Smart-Meter-Rohdaten (Excel).

Erkennt die drei vorkommenden Schema-Varianten automatisch und normalisiert
auf ein einheitliches Zielschema:

    Index   : MultiIndex (meter_id, timestamp)  – timestamp tz-aware Europe/Berlin
    Spalten : value_kw     (float, Leistung in kW; kWh-Dateien werden umgerechnet)
              is_substitute (bool, True = Ersatzwert laut Status-Flag)

Quellformate
------------
- Lastgang     : Spalten 'Datum/Zeit', 'Wert [kWh]', 'Status'  -> Energie kWh + Qualitäts-Flag
- ZRV          : Spalten 'Einheit' (=Timestamp), 'kW'          -> Leistung kW, Header in Zeile 1
- ZRV-mit-Kopf : wie ZRV, aber Leerzeilen/Metadaten-Block vor dem Header

Der Loader lädt und normalisiert ausschließlich. Keine Anomalie-Logik.

`load_category` vergibt stabile meter_ids (Baumarkt_01, ...) über eine
persistente Mapping-Datei. Bestehende IDs werden nie umnummeriert; neue
Dateien werden hinten angehängt. Bewusstes Neuaufsetzen via CLI:

    python -m src.eda.loader --remap-category Baumärkte
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = _PROJECT_ROOT / "data" / "raw"
MAPPING_PATH = _PROJECT_ROOT / "data" / "processed" / "_meter_id_mapping.csv"
SITES_PATH = _PROJECT_ROOT / "config" / "sites.yaml"

# Felder, die bei fehlender Site-Angabe auf die Würzburg-Defaults zurückfallen.
_DEFAULTABLE_FIELDS = ("lat", "lon", "bundesland")

_MAPPING_COLUMNS = ["meter_id", "filename", "source_meta_id", "category", "n_observations"]

# Kategorie -> Singular-Präfix für die meter_id.
_CATEGORY_PREFIX = {
    "Baumärkte": "Baumarkt",
    "Ladestationen": "Ladestation",
    "Tankstellen": "Tankstelle",
    "Büro": "Büro",
    "Handel": "Handel",
}

# Bekannte Müll-Dateien, die nie geladen werden (zusätzlich zu ~$-Lockdateien).
SKIP_FILES = {"Lastgang_36_2023-01-01-2025-12-31.xlsx"}

_TZ = "Europe/Berlin"


# --------------------------------------------------------------------------- #
# Site-Konfiguration (config/sites.yaml) mit Würzburg-Defaults
# --------------------------------------------------------------------------- #
def load_sites(path: str | Path = SITES_PATH) -> dict:
    """Lädt config/sites.yaml (defaults + sites)."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def resolve_site(
    site_id: str, sites: dict | None = None, path: str | Path = SITES_PATH
) -> dict:
    """Site-Metadaten inkl. optionalem Fallback auf einen `defaults:`-Block.

    Fehlt eines der Felder lat/lon/bundesland auf Site-Ebene (oder ist null) und
    existiert ein `defaults:`-Block, wird der Wert von dort übernommen und eine
    WARNING geloggt – so ist beim Pipeline-Lauf sofort sichtbar, welche Standorte
    auf einen Default fallen. Der reguläre Datenstand pflegt für jeden Standort
    echte PLZ-Koordinaten, sodass dieser Pfad nicht mehr greift.
    """
    data = sites if sites is not None else load_sites(path)
    defaults = data.get("defaults", {})
    site = next((s for s in data.get("sites", []) if s.get("id") == site_id), None)
    if site is None:
        raise KeyError(f"Site '{site_id}' nicht in sites.yaml gefunden.")

    merged = dict(site)
    fell_back = False
    for field in _DEFAULTABLE_FIELDS:
        if merged.get(field) is None:
            merged[field] = defaults.get(field)
            fell_back = True
    if fell_back:
        merged["lat_lon_source"] = defaults.get("lat_lon_source", "default")
        logger.warning(
            "Using default coords from sites.yaml defaults for site=%s", site_id
        )
    return merged


# --------------------------------------------------------------------------- #
# Schema-Erkennung
# --------------------------------------------------------------------------- #
def _find_header_row(raw: pd.DataFrame) -> int | None:
    """Erste Zeile, deren erste Zelle 'Datum/Zeit' oder 'Einheit' ist bzw. die
    'Wert [kWh]' enthält. Damit fällt ein Leerzeilen-/Metadaten-Vorspann weg."""
    for i in range(min(40, len(raw))):
        row = [str(x).strip() for x in raw.iloc[i].tolist()]
        if row and row[0] in ("Datum/Zeit", "Einheit"):
            return i
        if "Wert [kWh]" in row:
            return i
    return None


def _extract_meta_id(path: Path) -> str:
    """Markt-/Messlokations-ID aus dem Metadaten-Vorspann, sonst "".

    Marktlokation wird bevorzugt. Wird nur fürs Mapping benutzt – diese ID
    landet nie in einem geladenen Analyse-DataFrame.
    """
    raw = pd.read_excel(path, header=None, nrows=40)
    hdr = _find_header_row(raw)
    limit = hdr if hdr is not None else len(raw)
    found: dict[str, str] = {}
    if raw.shape[1] < 2:
        return ""
    for i in range(limit):
        label = str(raw.iloc[i, 0]).strip()
        if label in ("Marktlokation", "Messlokation"):
            val = raw.iloc[i, 1]
            if pd.notna(val):
                found[label] = str(val).strip()
    return found.get("Marktlokation") or found.get("Messlokation") or ""


# --------------------------------------------------------------------------- #
# Zeitzone
# --------------------------------------------------------------------------- #
def _localize(idx: pd.DatetimeIndex, label: str) -> pd.DatetimeIndex:
    """Naive Timestamps auf Europe/Berlin lokalisieren. DST-robust.

    Konvention (bewusst dokumentiert, weil sie das Verhalten an den
    DST-Wenden festlegt):

    - Herbst-Rückstellung (mehrdeutige Stunde, jede Wanduhrzeit doppelt):
      Die erste (chronologisch frühere) Belegung gilt als Sommerzeit
      (DST=True), die zweite als Winterzeit. Umgesetzt über
      ``ambiguous = ~idx.duplicated(keep="first")``; ``idx`` ist hier bereits
      aufsteigend sortiert, "erste Belegung" ist also die DST-Stunde.
    - Frühjahrs-Vorstellung (nicht existierende Stunde 02:00–03:00):
      ``nonexistent="shift_forward"`` – ein solcher Zeitstempel wird auf den
      nächsten gültigen Moment nach vorn geschoben.

    Warum nicht ``ambiguous='infer'`` (wie ursprünglich angedacht): pandas'
    ``infer`` funktioniert nur über genau EINEN DST-Übergang und scheitert an
    mehrjährigen Reihen mit Lücken (Fehler "N dst switches when there should
    only be 1"). Es liefe damit faktisch immer in den Fallback
    ``ambiguous=False`` – genau die stille Fehlbehandlung der doppelten
    Stunde, die wir vermeiden wollen. Die explizite Regel oben ist das, was
    ``infer`` versucht, nur robust gegen Lücken.
    """
    if idx.tz is not None:
        return idx
    ambiguous = ~idx.duplicated(keep="first")
    try:
        return idx.tz_localize(_TZ, ambiguous=ambiguous, nonexistent="shift_forward")
    except Exception as exc:  # nur noch echte Pathologien
        logger.warning("DST-Fallback für %s: %s; nutze ambiguous=False.", label, exc)
        return idx.tz_localize(_TZ, ambiguous=False, nonexistent="shift_forward")


# --------------------------------------------------------------------------- #
# Einzeldatei
# --------------------------------------------------------------------------- #
def load_smartmeter(path: str | Path, meter_id: str | None = None) -> pd.DataFrame:
    """Lädt eine Smart-Meter-Datei und normalisiert auf das Zielschema.

    Parameters
    ----------
    path : Pfad zur .xlsx-Datei.
    meter_id : optionaler Identifier. Ohne Angabe = Dateiname ohne Endung.
        Keine Mapping-Logik – die passiert ausschließlich in `load_category`.

    Returns
    -------
    DataFrame, MultiIndex (meter_id, timestamp), Spalten [value_kw, is_substitute].
    """
    path = Path(path)
    mid = meter_id if meter_id is not None else path.stem

    raw = pd.read_excel(path, header=None)
    hdr = _find_header_row(raw)
    if hdr is None:
        raise ValueError(f"Kein bekanntes Schema in {path.name} gefunden.")

    cols = [str(c).strip() for c in raw.iloc[hdr].tolist()]
    data = raw.iloc[hdr + 1 :].copy()
    data.columns = cols

    ts_col = cols[0]
    if "Wert [kWh]" in cols:
        value_col, unit = "Wert [kWh]", "kWh"
    elif "kW" in cols:
        value_col, unit = "kW", "kW"
    else:
        raise ValueError(f"Keine Wert-Spalte (kW/kWh) in {path.name}: {cols}")

    ts = pd.to_datetime(data[ts_col], errors="coerce", dayfirst=True)
    val = pd.to_numeric(data[value_col], errors="coerce")
    if "Status" in cols:
        is_sub = ~data["Status"].astype(str).str.contains("Wahrer Wert", na=False)
    else:
        is_sub = pd.Series(False, index=data.index)

    mask = ts.notna()
    out = pd.DataFrame(
        {
            "timestamp": ts[mask].to_numpy(),
            "value": val[mask].to_numpy(),
            "is_substitute": is_sub[mask].to_numpy(),
        }
    ).sort_values("timestamp")

    if unit == "kWh":
        diff = out["timestamp"].diff().median()
        interval_h = (
            diff.total_seconds() / 3600 if pd.notna(diff) and diff.total_seconds() > 0 else 0.25
        )
        out["value_kw"] = out["value"] / interval_h
    else:
        out["value_kw"] = out["value"]

    idx = pd.MultiIndex.from_arrays(
        [[mid] * len(out), _localize(pd.DatetimeIndex(out["timestamp"]), mid)],
        names=["meter_id", "timestamp"],
    )
    result = pd.DataFrame(
        {
            "value_kw": out["value_kw"].to_numpy(),
            "is_substitute": out["is_substitute"].astype(bool).to_numpy(),
        },
        index=idx,
    )
    return result.sort_index()


# --------------------------------------------------------------------------- #
# Mapping-Helfer
# --------------------------------------------------------------------------- #
def _read_mapping(mapping_path: Path) -> pd.DataFrame:
    if mapping_path.exists():
        df = pd.read_csv(mapping_path, dtype={"source_meta_id": str})
        return df.reindex(columns=_MAPPING_COLUMNS).fillna({"source_meta_id": ""})
    return pd.DataFrame(columns=_MAPPING_COLUMNS)


def _id_num(meter_id: str) -> int:
    m = re.search(r"_(\d+)$", str(meter_id))
    return int(m.group(1)) if m else 0


# --------------------------------------------------------------------------- #
# Kategorie
# --------------------------------------------------------------------------- #
def load_category(
    name: str,
    remap: bool = False,
    raw_dir: str | Path = RAW_DIR,
    mapping_path: str | Path = MAPPING_PATH,
) -> pd.DataFrame:
    """Lädt alle Dateien einer Kategorie als ein DataFrame mit stabilen meter_ids.

    Stabilitätsgarantie: bestehende IDs werden wiederverwendet, neue Dateien
    hinten angehängt, fehlende Dateien als Lücke geloggt (kein Reindex).
    `remap=True` setzt das Mapping dieser Kategorie bewusst neu auf.
    """
    raw_dir = Path(raw_dir)
    mapping_path = Path(mapping_path)
    cat_dir = raw_dir / name

    present = sorted(
        p
        for p in cat_dir.glob("*.xlsx")
        if not p.name.startswith("~$") and p.name not in SKIP_FILES
    )
    present_names = {p.name for p in present}

    mapping = _read_mapping(mapping_path)
    if remap:
        mapping = mapping[mapping["category"] != name].copy()
        cat_existing: dict[str, str] = {}
        next_num = 1
    else:
        cat_rows = mapping[mapping["category"] == name]
        cat_existing = dict(zip(cat_rows["filename"], cat_rows["meter_id"], strict=False))
        next_num = max((_id_num(m) for m in cat_rows["meter_id"]), default=0) + 1

    prefix = _CATEGORY_PREFIX.get(name, name)

    missing = sorted(fn for fn in cat_existing if fn not in present_names)
    for fn in missing:
        logger.warning(
            "Mapping-Lücke: %s (%s) nicht mehr im Ordner; ID bleibt reserviert.",
            cat_existing[fn],
            fn,
        )

    new_assignments: dict[str, str] = {}
    for p in present:  # present ist sortiert -> deterministische Vergabe
        if p.name in cat_existing:
            continue
        new_assignments[p.name] = f"{prefix}_{next_num:02d}"
        next_num += 1

    logger.info("Kategorie %s: %d Datei(en) gefunden.", name, len(present))
    logger.info("%d neue meter_id(s) vergeben.", len(new_assignments))
    logger.info("%d Lücke(n) im Mapping erkannt.", len(missing))

    frames: list[pd.DataFrame] = []
    records: list[dict] = []
    for p in present:
        mid = cat_existing.get(p.name) or new_assignments[p.name]
        df = load_smartmeter(p, meter_id=mid)
        if df.empty or df["value_kw"].fillna(0).abs().sum() == 0:
            logger.warning("Übersprungen (leer/null): %s", p.name)
            continue
        frames.append(df)
        records.append(
            {
                "meter_id": mid,
                "filename": p.name,
                "source_meta_id": _extract_meta_id(p),
                "category": name,
                "n_observations": len(df),
            }
        )

    loaded_names = {r["filename"] for r in records}
    keep = mapping[~((mapping["category"] == name) & (mapping["filename"].isin(loaded_names)))]
    updated = pd.concat([keep, pd.DataFrame(records, columns=_MAPPING_COLUMNS)], ignore_index=True)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    updated.to_csv(mapping_path, index=False)

    if not frames:
        return pd.DataFrame(
            {"value_kw": pd.Series(dtype=float), "is_substitute": pd.Series(dtype=bool)},
            index=pd.MultiIndex.from_arrays([[], []], names=["meter_id", "timestamp"]),
        )
    return pd.concat(frames).sort_index()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _main(argv: list[str] | None = None) -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remap-category",
        metavar="NAME",
        help="Mapping dieser Kategorie bewusst neu aufbauen (frische Nummerierung).",
    )
    args = parser.parse_args(argv)

    if args.remap_category:
        df = load_category(args.remap_category, remap=True)
        n_meter = df.index.get_level_values("meter_id").nunique()
        print(f"Remap {args.remap_category}: {n_meter} meter, {len(df)} Zeilen.")
    else:
        parser.print_help()


if __name__ == "__main__":
    _main()
