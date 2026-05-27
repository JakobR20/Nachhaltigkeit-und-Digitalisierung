# Daten-Schema der RLM-Lastgänge

Die Rohdaten von Rausch liegen als **eine Excel-Datei pro Standort** vor (gitignored unter
`data/raw/rlm/`). Es treten **zwei Wert-Formate** und **drei Datei-Layouts** auf; der Loader
(`rausch_energy_anomaly.ingestion.rlm_loader`) erkennt sie automatisch und normalisiert auf
ein einheitliches Zielschema.

## Zielschema (nach dem Loader)

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| Index `meter_id` | str | stabile Standort-/Zähler-ID (über Mapping persistiert) |
| Index `timestamp` | datetime, tz-aware **Europe/Berlin** | 15-min-Raster |
| `value_kw` | float | Leistung in **kW** (kWh-Quellen werden umgerechnet) |
| `is_substitute` | bool | True = Ersatzwert / ungültiger Status (nur Lastgang-Format); bei reinen kW-Dateien immer False |

**Status-Flag-Regel:** Werte mit gültigem Status gehen ins Modelltraining; markierte
Ersatzwerte (`is_substitute = True`) werden **beibehalten** (nicht gelöscht) und stehen der
Diagnose zur Verfügung, aber nicht dem Training.

## Format A – ZRV (Leistung in kW)

- Spalten: `Einheit` (= Zeitstempel `DD.MM.YYYY HH:MM:SS`), `kW`.
- **Header-Position variiert** – teils Zeile 0, teils nach mehreren Leerzeilen / einem
  Metadaten-Vorspann (`Verwendungsart`, `Mess-/Marktlokation`). Loader sucht die Header-Zeile
  dynamisch (`Spalte0 == 'Einheit'`).
- Kein Status-Flag → `is_substitute = False`.

## Format B – Lastgang (Energie in kWh, mit Status)

- Spalten: `Datum/Zeit`, `Wert [kWh]`, `Status`.
- Energie pro 15-min-Intervall → Umrechnung `value_kw = wert_kwh / 0.25`.
- `Status`: `'Blank' Wahrer Wert (MC)` = gültig; `Ersatzwert (MC)` = ersetzt → `is_substitute = True`.

## Einheiten & Auflösung

- Zielgröße **kW** (Leistung). Energie: `energy_kwh = value_kw * 0.25` pro 15-min-Intervall.
- Auflösung: **15 Minuten** (~105.120 Punkte pro Standort und Jahr).

## Zeitraum

- **01.01.2023 00:00 – 13.03.2026** Europe/Berlin (erweitert ggü. Brief §4.3, der bis
  31.12.2025 reichte – reales Inventar geht weiter).

## Zeitzone & DST

- Lokale Zeit **Europe/Berlin** (nicht UTC).
- Herbst-Rückstellung: erste Belegung doppelter Wanduhrzeit = Sommerzeit, zweite = Winterzeit
  (`ambiguous = ~duplicated(keep="first")`).
- Frühjahr: nicht existierende Stunde → `nonexistent="shift_forward"`.
- Loader loggt DST-Fallbacks pro Datei.

## Externe Daten (separat gecacht)

- Wetter (Bright Sky/DWD) und Strompreis (Energy-Charts, DE-LU) liegen stündlich in **UTC**
  vor; vor dem Join auf Europe/Berlin konvertieren. EPEX wechselt ab 2025 von stündlicher auf
  viertelstündliche Auflösung → vor dem Join auf gemeinsame Frequenz resampeln.
