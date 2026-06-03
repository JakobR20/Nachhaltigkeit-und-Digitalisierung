# Poster-Outline — A1 Querformat (841 × 594 mm)

> **Layout-Skelett**, abgeleitet aus dem Paper-Skelett (`paper/00_outline.md` ff.).
> Nur Block-Struktur, Kernaussagen, Visualisierungs-Verweise und Wort-Budgets —
> **kein Fließtext**. Der finale Druck wird später in einem Design-Tool gebaut
> (siehe „Poster-Tools" am Ende). Eigenständige 50-%-Leistung, keine verkleinerte
> Paper-Kopie (THWS-Skill).

## Spaltenwahl: drei Spalten — Begründung

**Gewählt: 3 Spalten + durchgehender Header + durchgehender Footer.**

- A1 quer = **841 mm breit**. Drei Spalten à ~250 mm + 2 Gutter à ~20 mm + 2×25 mm
  Randmarge passen sauber; vier Spalten à ~185 mm würden die breiten Ergebnis-Plots
  (κ-Heatmap, X-Sweep) und die LLM-Beispielkarte zu schmal quetschen.
- Das „vier Methoden + Ensemble"-Argument ist **ein visueller Block** (Methodik-Diagramm
  mit 4 Strängen → Union), nicht vier Spalten. Die Erzählung ist
  **Problem → Methode/Daten → Ergebnis/LLM**, was natürlich auf drei Spalten fällt.
- Whitespace bei A1 großzügig halten — drei Spalten lesen sich ruhiger als vier.

---

## Layout-Schema (ASCII, nicht maßstabsgetreu)

```
+===========================================================================+
| HEADER  (~80 mm)                                                          |
| [THWS-Logo]   KI-gestützte Anomalieerkennung in Smart-Meter-Daten         |
|               Ensemble-Methoden & LLM-Handlungsempfehlungen …             |
|               Felix Zorn · Jakob Ringel — Nachhaltigkeit & Digitalisierung|
+-------------------+-------------------------+-------------------------------+
| LINKE SPALTE      | MITTLERE SPALTE         | RECHTE SPALTE                 |
| ~250 mm           | ~250 mm                 | ~250 mm                      |
|                   |                         |                              |
| 1 Motivation      | 4 Datenbasis            | 6 LLM-Pipeline               |
|   [Karte/Icon]    |   [Mini-Tab/Icons]      |   [Empfehlungs-Karte]        |
|                   |                         |                              |
| 2 Forschungsfrage | 5 Ergebnisse            | 7 Dashboard-Screenshot       |
|   (groß)          |   [06_kappa_heatmap]    |   [dashboard_screenshots/]   |
|                   |   [06_sweep_flag_rates] |                              |
| 3 Methodik-       |                         | 8 Fazit (groß)               |
|   Übersicht       |                         |   + Limitations-Mini-Zeile   |
|   [Flow: 4→Union] |                         | 9 [QR Repo]                  |
+-------------------+-------------------------+-------------------------------+
| FOOTER (~30 mm)  Quellen kompakt · Repo-Link · Acknowledgment Rausch       |
+===========================================================================+
```

---

## Header (durchgehend oben, ~80 mm)

- **THWS-Logo** links; rechts optional Rausch-Logo (sobald geliefert).
- **Titel** (zentriert, ~60–72 pt): „KI-gestützte Anomalieerkennung in
  Smart-Meter-Daten" *(finaler Titel = User-Entscheidung)*.
- **Untertitel** (~36 pt): „Ensemble-Methoden und LLM-Handlungsempfehlungen für
  Energiemanagement".
- **Autoren:** Felix Zorn, Jakob Ringel.
- **Modul + Datum:** „Nachhaltigkeit und Digitalisierung · FIW THWS · Prof. Dr. M. Müßig · 2026".
- Wort-Budget: ~25 (reine Kopfzeilen).

---

## Linke Spalte

### Block 1 — Motivation / Hintergrund
- **Kernaussage:**
  - Energiewende + Smart-Meter-Rollout (GNDEW 2023) → datengetriebene Effizienz im Gewerbe.
  - Vermeidbarer Verbrauch bleibt ohne Analyse unsichtbar; Rausch liefert reale RLM-Daten.
- **Visualisierung:** kleines Icon/Karten-Element (Strom/Gebäude) oder DE-Karte mit
  Würzburg-Marker. *(eigene Skizze, keine Repo-Datei)*
- **Wort-Budget:** ~50.

### Block 2 — Forschungsfrage
- **Kernaussage (eine zentrale Frage, groß gesetzt, ~32–40 pt):**
  - „Wie lassen sich Anomalien im gewerblichen Lastgang erklärbar und ohne
    pro-Standort-Training erkennen — und automatisiert in Handlungsempfehlungen überführen?"
- **Visualisierung:** keine; als Eyecatcher-Typo / farbiger Kasten.
- **Wort-Budget:** ~25.

### Block 3 — Methodik-Übersicht
- **Kernaussage:**
  - Vier Methoden, vier Signalfamilien: **Z-Score** (Punkt-Outlier), **ARIMA** (Forecast-Abweichung),
    **Cluster-Distanz** (Segment-Form), **Autoencoder** (Rekonstruktionsfehler).
  - Zusammengeführt per **Union-Ensemble** → Empfehlung des Papers.
- **Visualisierung:** Methodik-Flowchart (eigener Plot/Skizze): RLM → STL/Features →
  4 Methoden-Stränge → Union → LLM-Empfehlung. Methoden in den Projektfarben
  (`config/dashboard.yaml`: zscore `#1f77b4`, arima `#d62728`, cluster `#2ca02c`,
  autoencoder `#9467bd`). Optional Beispiel `reports/figures/05_smoke_anomalien_je_methode.png`.
- **Wort-Budget:** ~80.

---

## Mittlere Spalte

### Block 4 — Datenbasis
- **Kernaussage:**
  - 22+1 Baumärkte, RLM-Lastgänge 15-min, 2023-01 bis ~2026-03.
  - Train/Test-Split vor/nach 2025-01-01; Würzburg-Wetterreferenz (PLZ ausstehend).
- **Visualisierung:** kompakte Tabelle oder Icon-Reihe (Standorte / Auflösung /
  Zeitraum / externe Quellen Wetter+Preis). *(eigene Darstellung)*
- **Wort-Budget:** ~40.

### Block 5 — Ergebnisse (Hauptbefunde)
- **Kernaussage (Klartext):**
  - „Methoden komplementär: κ ≈ 0 über alle Paare (max 0,11) → disjunkte Anomalie-Mengen."
  - „Sweet-Spot bei X = 0,25: ARIMA und AE im Zielband, Z-Score streut breiter."
  - „Precision 100 % über alle vier Methoden auf den Top-Kandidaten."
- **Visualisierung (2 große Plots):**
  - `reports/figures/06_kappa_heatmap.png` (κ-Komplementarität).
  - `reports/figures/06_sweep_flag_rates.png` (Flag-Rate über `threshold_pct`).
  - Optional Mini-Tabelle Inferenzkosten aus `reports/tables/06_method_comparison.md`
    (AE ~20× schneller als ARIMA).
- **Wort-Budget:** ~100.

---

## Rechte Spalte

### Block 6 — LLM-Pipeline
- **Kernaussage:**
  - Lokales **Qwen 2.5 7B** (Ollama), JSON-Schema-erzwungen + Pydantic-validiert.
  - **66/66 erfolgreich, 0 Retries, 0 Schema-Fehler**, 6,6 s/Anomalie; Kontext (Wetter,
    Preis, Mehrkosten) deterministisch im Code berechnet.
- **Visualisierung:** Empfehlungs-Karte aus einer echten Ausgabe
  (`reports/llm_recommendations/001.json`, Baumarkt_03, nachts):
  - Last 72,6 kW vs. erwartet 8,0 kW (**+807 %**), Mehrkosten **31,35 €** / ~6 h.
  - Ursache: „Nachtabsenkung der HVAC nicht eingehalten" · Schweregrad **hoch** · Konfidenz 0,85.
  - 3 Maßnahmen (HVAC-Zeitprogramme prüfen, Wartung, Lüftung abschalten).
  - Severity-Farbe aus `config/dashboard.yaml` (hoch `#d62728`).
- **Wort-Budget:** ~80.

### Block 7 — Dashboard-Screenshot
- **Kernaussage:**
  - Operatives Artefakt für Rausch: Anomalien priorisiert nach Kosten/Schweregrad,
    Re-Thresholding über Slider ohne Neu-Inferenz.
- **Visualisierung:** Screenshot aus `reports/dashboard_screenshots/`
  (Stakeholder-/Übersichtsansicht). Falls keine geeignete Ansicht: **Platzhalter-Box**.
- **Wort-Budget:** ~30.

### Block 8 — Fazit / Kernaussage
- **Kernaussage (groß, ~32 pt):**
  - „Kein einzelner Detektor gewinnt — ein **Union-Ensemble** aus vier komplementären
    Methoden plus lokale LLM-Empfehlung macht vermeidbaren Verbrauch sichtbar und handhabbar."
  - **Limitations-Mini-Zeile** (klein): HVAC-Default-Hypothese als Prüfauftrag · zentrale
    Wetterreferenz · Übertragbarkeit nur innerhalb Kategorie.
- **Visualisierung:** keine (Typo-Block, optional SDG-7/9-Icons als Nachhaltigkeitsbezug).
- **Wort-Budget:** ~60.

### Block 9 — Kontakt / QR
- **Kernaussage:** QR-Code zum Repo, klein, unten rechts.
- **Visualisierung:** QR (generiert), Beschriftung „GitHub: JakobR20/Nachhaltigkeit-und-Digitalisierung".
- **Wort-Budget:** ~5.

---

## Footer (durchgehend unten, ~30 mm)

- **Quellen kompakt (3–5 aus `paper/references.bib`):** Chandola et al. (2009);
  Cleveland et al. (1990); Pang et al. (2021); Cohen (1960); Qwen Team (2024).
- **Repo-Link** (privat, ohne URL): „GitHub: JakobR20/Nachhaltigkeit-und-Digitalisierung".
- **Acknowledgment:** „Datengrundlage und methodisches Feedback: Rausch Technology."
- **Wort-Budget:** ~30.

---

## Wort-Budget gesamt

| Block | Wörter |
|---|---|
| Header | ~25 |
| 1 Motivation | ~50 |
| 2 Forschungsfrage | ~25 |
| 3 Methodik-Übersicht | ~80 |
| 4 Datenbasis | ~40 |
| 5 Ergebnisse | ~100 |
| 6 LLM-Pipeline | ~80 |
| 7 Dashboard | ~30 |
| 8 Fazit | ~60 |
| 9 Kontakt | ~5 |
| Footer | ~30 |
| **Summe** | **~525** — typisch für A1 |

## Visuelle Verteilung

- Ziel **~60 % Visualisierung / ~40 % Text**. Pro Spalte 2–3 große visuelle Elemente:
  - Links: Motiv-Icon/Karte · Methodik-Flowchart.
  - Mitte: κ-Heatmap · X-Sweep (· Mini-Kostentabelle).
  - Rechts: LLM-Empfehlungs-Karte · Dashboard-Screenshot (· QR).

---

## Layout-Empfehlungen

- **Schriftgrößen** (lesbar aus ~1,5 m): Titel ≥ 60 pt, Section-Header ≥ 32 pt,
  Body ≥ 24 pt, Footer/Quellen ≥ 18 pt.
- **Farben** konsistent mit Dashboard (`config/dashboard.yaml`): Methodenfarben
  (zscore `#1f77b4`, arima `#d62728`, cluster `#2ca02c`, autoencoder `#9467bd`),
  Severity (hoch `#d62728`, mittel `#ff7f0e`, niedrig `#2ca02c`).
- **Whitespace** großzügig — bei A1 wirken überfüllte Poster gedrungen.
- **THWS-Designvorgaben:** prüfen, ob Müßig/THWS eine offizielle Poster-Vorlage oder
  CD-Vorgaben (Logo, Farben, Schrift) stellt — falls ja, diese befolgen. *(User-Check)*
- Abbildungen mind. 1500 px breit, Achsen mit Einheit, eigene Plots „Eigene Darstellung".

## Poster-Tools

- **Standard:** LaTeX mit `beamerposter` oder `tikzposter` (A1, `orientation=landscape`).
- **Alternative:** Affinity Publisher / Adobe InDesign.
- **Schnell:** PowerPoint mit A1-Seiteneinrichtung (84,1 × 59,4 cm) oder Canva-A1-Template.
