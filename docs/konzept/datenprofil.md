# Datenprofil – Smart-Meter-Rohdaten

> Stand: 2026-05-20 · Quelle: `data/raw/` (von RAUSCH via OneDrive) · erstellt im Rahmen der EDA (Skill `smart-meter-eda`).
> Inventar maschinell erzeugt: `data/raw/_inventar.csv` (nicht im Repo, DSGVO).

## 1. Überblick

77 Excel-Dateien in fünf Liegenschafts-Kategorien. **75 davon sind verwertbar**, alle in **15-Minuten-Auflösung** mit **naiven Timestamps** (keine Zeitzone hinterlegt).

| Kategorie | Dateien (verwertbar) | Einheit | Zeitraum (frühestes → spätestes) |
|-----------|----------------------|---------|----------------------------------|
| Baumärkte | 26 | kW | 2023-01-01 → 2026-03-13 |
| Büro | 1 | kW | 2023-01-01 → 2025-12-31 |
| Handel | 5 (kW) + 3 (kWh) | kW / kWh | 2023-01-01 → 2025-12-31 |
| Ladestationen | 25 (kW) + 1 (kWh) | kW / kWh | 2023-01-01 → 2025-12-31 |
| Tankstellen | 14 (kW) | kW | 2023-01-01 → 2025-12-31 |

## 2. Drei Quellformate

Die Dateien stammen aus zwei unterschiedlichen Exports und kommen in drei Layouts:

**A – `Lastgang_*.xlsx`** (4 Dateien, davon 3 nutzbar)
- Spalten: `Datum/Zeit`, `Wert [kWh]`, `Status`
- **Energie in kWh pro 15-Min-Intervall** (kumulierter Verbrauch im Intervall).
- `Status` ist ein **Qualitäts-Flag**: `'Blank' Wahrer Wert (MC)` = echte Messung, `Ersatzwert (MC)` = ersetzter/interpolierter Wert. Über die 3 Lastgang-Dateien: **435 Ersatzwerte**.

**B – `Zeitreihenvisualisierung_*.xlsx`, Header in Zeile 1** (Mehrheit)
- Spalten: `Einheit` (= Timestamp, trotz des Namens!), `kW`
- **Momentanleistung in kW**, kein Qualitäts-Flag.

**C – `Zeitreihenvisualisierung_*.xlsx` mit Vorspann** (Baumärkte; einige Ladestationen)
- Wie B, aber mit Leerzeilen bzw. einem Metadaten-Block (`Verwendungsart`, `Messlokation`, `Marktlokation`, …) vor dem eigentlichen Header.
- **Loader muss die Header-Zeile dynamisch suchen** (`Einheit`/`Datum/Zeit`), sonst werden Metadaten-IDs als Messwerte fehlinterpretiert.

## 3. Einheiten-Mix: kWh vs. kW

Der kritische Punkt für jede gemeinsame Analyse:

- **kWh** (Lastgang) = Energie pro Intervall.
- **kW** (ZRV) = Momentanleistung.
- Umrechnung bei 15-Min-Raster: `kWh = kW × 0,25` bzw. `kW = kWh / 0,25`.

→ Vor der Methodenanwendung **eine Zieleinheit festlegen** und konsequent umrechnen. Nicht kWh- und kW-Reihen ungeprüft mischen.

## 4. Datenqualität

- **Auflösung:** durchgängig 15 min (Median der Zeitdifferenz) bei allen 75 Dateien.
- **Zeitzone:** naive Timestamps → **DST-Übergänge** (März/Oktober) sind ein Risiko; beim Reindexing auf eine feste Frequenz prüfen, ob doppelte/fehlende Stunden auftreten. Behandlung siehe unten.
- **Variierende Startdaten:** nicht alle Reihen decken den vollen Zeitraum ab (z. B. Baumarkt-Zähler ab 2024-04-19, Handel-Lastgang ab 2024-11, Ladestation-kWh ab 2025-01-22). Vor Querschnittsvergleichen auf gemeinsamen Zeitraum zuschneiden.
- **Ersatzwerte:** nur in den Lastgang-Dateien als Flag erkennbar (435 Stück). Bei den kW-Dateien gibt es kein Flag → ersetzte Werte sind dort nicht von echten unterscheidbar.

### Zeitzonen-Behandlung

Die Rohdaten kommen **naiv** (ohne Zeitzone) und stehen in lokaler Wanduhrzeit. Der Loader (`src/eda/loader.py`) lokalisiert sie auf **Europe/Berlin** mit fester Konvention an den DST-Wenden:

- **Herbst-Rückstellung** (mehrdeutige Stunde, jede Uhrzeit doppelt): erste Belegung = Sommerzeit (DST), zweite = Winterzeit.
- **Frühjahrs-Vorstellung** (nicht existierende Stunde): `nonexistent="shift_forward"` – Zeitstempel rückt auf den nächsten gültigen Moment.

Statt `ambiguous='infer'` setzen wir die Regel explizit, weil `infer` über mehrjährige Reihen mit Lücken scheitert und still falsch lokalisieren würde.

### Auszusortieren

| Datei | Problem |
|-------|---------|
| `Tankstellen/Lastgang_36_2023-01-01-2025-12-31.xlsx` | Komplett 0 / leer (2880 Zeilen, alle Null). |
| `Tankstellen/~$Lastgang_36_…xlsx` | Excel-Lock-/Tempdatei (`~$`), keine Daten. |

### Flache Baumarkt-Zähler (`vmax < 1 kW`) — mit Marja zu klären

Befund aus `notebooks/01_eda.ipynb` (Block 2b): **3 von 26** Baumarkt-Zählern haben einen unplausibel niedrigen Maximalwert unter 1 kW.

**Betroffene meter_ids:** `Baumarkt_01`, `Baumarkt_02`, `Baumarkt_04`
(Mapping → Originaldatei in `data/processed/_meter_id_mapping.csv`.)

Hypothesen: (a) **Einheiten-Bug Faktor 1000** (W statt kW) — nach `× 1000` lägen die Maxima im plausiblen Bereich der übrigen Zähler, daher die wahrscheinlichste Erklärung; (b) **Teilstrang-/Unterzähler** (korrekt, aber nicht mit Hauptzählern vergleichbar); (c) **dauerhaft defekt**.

**Empfehlung:** vorerst aus der Hauptanalyse **ausschließen** (nicht löschen) und **mit Marja klären** (Einheit W vs. kW? Unterzähler?). Referenz für die Hausarbeit.

## Externe Daten (Wetter & Preise)

Beschafft über `python -m src.apis.fetch_context` (Clients in `src/apis/`, Cache in `data/external/`, Ergebnis in `data/processed/`, beides gitignored). Zeitraum aus dem kompletten Baumarkt-Datensatz abgeleitet (2023-01-01 bis 2026-03-13).

| Datei | Quelle | Inhalt | Umfang |
|-------|--------|--------|--------|
| `weather.parquet` | DWD via Brightsky | `temperature` (°C), `dew_point`, `wind_speed`, `solar`/Strahlung, `hdd` (= max(15 − temp, 0)), u. a.; Index UTC, stündlich | ~28.000 Zeilen, −11,2…36,6 °C, keine Zeit-Lücken |
| `prices.parquet` | EPEX-SPOT via energy-charts (DE-LU) | `price_eur_mwh`; Index UTC | ~39.800 Zeilen, −500…936 €/MWh, keine Lücken |

Hinweise:
- **Temperatur-Einheit:** Brightsky liefert mit `units=si` **Kelvin**; der Client rechnet auf °C um (sonst wäre HDD durchgängig 0). HDD wird direkt als Feature mitgeführt.
- **Preis-Auflösung gemischt:** bis 2024 stündlich, ab 2025 viertelstündlich (Marktumstellung Day-Ahead DE-LU). Die Preisreihe hat also keine konstante Frequenz. **Vor dem Join** explizit auf eine gemeinsame Zielfrequenz resampeln (z. B. `prices.resample("1h").mean()`), statt konstante Auflösung anzunehmen — sonst doppelte/fehlende Zuordnungen.
- **Methodische Lernerfahrung (für die Diskussion zur Datenqualität):** Bei der DWD-Anbindung wurden zwei Bugs vor produktiver Nutzung gefixt: Einheit Kelvin→°C und Lücken an Chunk-Grenzen durch Überlappung. Das unterstreicht, dass externe APIs vor dem Vertrauen in die Daten validiert werden müssen.

### Standort-Proxy Würzburg (mit Marja zu klären)

Die tatsächlichen Standorte der Baumärkte sind noch unbekannt (Klärung im Call mit Marja nächste Woche). Bis dahin nutzen wir **Würzburg** (`DEFAULT_LAT/LON` aus `.env`: 49.7913, 9.9534) als Wetter-Proxy.

**Methodische Begründung:** Wetterereignisse in Deutschland sind räumlich stark korreliert (typische Skala mehrere hundert Kilometer); der Würzburg-Proxy verzerrt absolute Werte minimal, aber nicht die zeitliche Struktur, die für die Anomalieerkennung relevant ist.

## 5. Offene Punkte für die nächste Stufe (Methodenwahl)

Stand nach EDA (`notebooks/01_eda.ipynb`, Hauptscope Baumärkte):

1. **Scope steht:** Hauptdatensatz Baumärkte (kW), Validierung Handel/Lastgang_34 (kWh). Repräsentativer Zähler für Einzel-Plots: `Baumarkt_06`.
2. **Saisonalität bestätigt:** dominant **täglich + wöchentlich** (ACF-Peaks bei lag 24 / 168), Jahreskomponente sekundär.
3. **Form-Cluster:** k = 3 (über Silhouette gewählt) auf den 23 soliden Zählern — drei typische Tagesprofil-Muster.
4. **Vor Methodenanwendung offen:** flache Zähler ausschließen/klären (s. o.), Zeit-Lücken je Zähler behandeln, variierende Startdaten beachten.
5. **Externe Features:** Temperatur (DWD) und Kalender (Feiertage/Ferien) versprechen Mehrwert; Strompreis (EPEX) eher als Kontext. Korrelation noch ungetestet.
