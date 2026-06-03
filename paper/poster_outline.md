# Poster-Outline — A1 Querformat (841 × 594 mm)

> **Layout-Skelett**, abgeleitet aus dem Paper-Skelett (`paper/00_outline.md` ff.).
> Nur Block-Struktur, Kernaussagen, Visualisierungs-Verweise und Wort-Budgets —
> **kein Fließtext**. Der finale Druck wird später in einem Design-Tool gebaut
> (siehe „Poster-Tools" am Ende). Eigenständige 50-%-Leistung, keine verkleinerte
> Paper-Kopie.

## Struktur: Müßig-5-Element-Schema

**Pflicht-Aufbau (Müßig-Bewertung):** Einführung → Methode → Ergebnis →
Schlussfolgerung+Ausblick (**hervorgehoben**) → Referenzen.
Drei Spalten + durchgehender Header. **Kein Abstract, kein Kontakt/QR-Block**
(Müßig-Vorgabe). Lesefluss strikt Problem → Methode → Ergebnis → Schlussfolgerung.

### Spaltenwahl: drei Spalten

- A1 quer = **841 mm breit**. Drei Spalten à ~250 mm + 2 Gutter à ~20 mm + 2×25 mm
  Randmarge passen sauber; die breiten Ergebnis-Plots (κ-Heatmap, X-Sweep) brauchen
  die Spaltenbreite.
- Genau eine Spalte je Erzählschritt: links Einführung+Methode, Mitte Ergebnis,
  rechts Schlussfolgerung. Schlussfolgerung steht visuell isoliert rechts → leicht
  hervorzuheben.

---

## Layout-Schema (ASCII, nicht maßstabsgetreu)

```
+===========================================================================+
| HEADER  (~80 mm)                                                          |
| [THWS-Logo]   KI-gestützte Anomalieerkennung in Smart-Meter-Daten         |
|               Ensemble-Methoden & LLM-Handlungsempfehlungen …             |
|               Felix Zorn · Jakob Ringel — Nachhaltigkeit & Digitalisierung|
+-------------------+-------------------------+-------------------------------+
| SPALTE 1  ~250 mm | SPALTE 2  ~250 mm       | SPALTE 3  ~250 mm            |
|                   |                         |   +-------------------------+ |
| 1 EINFÜHRUNG      | 3 ERGEBNIS              |  | 4 SCHLUSSFOLGERUNG      | |
|   Hintergrund     |   Hauptbefund κ≈0       |  |   + AUSBLICK            | |
|   Ziel            |   [06_kappa_heatmap]    |  |   (HERVORGEHOBEN:       | |
|   Hypothese (groß)|   [06_sweep_flag_rates] |  |    Akzentfarbe, größer, | |
|                   |   LLM-Statistik         |  |    Font-Weight 700)     | |
| 2 METHODE         |   [LLM-Empfehlungs-     |  |   Kernaussage          | |
|   Stichprobe      |    Karte: 001.json]     |  |   Implikationen        | |
|   Design          |   (opt. Dashboard-Shot) |  |   Ausblick             | |
|   Messinstrumente |                         |  +-------------------------+ |
|   [Methodik-Flow] |                         |                              |
+-------------------+-------------------------+-------------------------------+
| FOOTER (~25 mm, klein/dezent)   5 REFERENZEN: Chandola 2009 · Cleveland 1990|
+===========================================================================+
```

---

## Header (durchgehend oben, ~80 mm)

- **THWS-Logo** links; rechts optional Rausch-Logo (sobald geliefert).
- **Titel** (zentriert, ~60–72 pt): „KI-gestützte Anomalieerkennung in
  Smart-Meter-Daten" *(finaler Titel = User-Entscheidung)*.
- **Untertitel** (~36 pt): „Ensemble-Methoden und LLM-Handlungsempfehlungen für
  Energiemanagement".
- **Autoren + Modul + Datum:** „Felix Zorn · Jakob Ringel — Nachhaltigkeit und
  Digitalisierung · FIW THWS · Prof. Dr. M. Müßig · 2026".
- Wort-Budget: ~25 (reine Kopfzeilen, nicht in der 520er-Summe).

---

## Spalte 1 (links, ~250 mm)

### Block 1 — Einführung
- **Theoretischer Hintergrund (kurz):**
  - Energiewende + Smart-Meter-Rollout (GNDEW 2023); KMU-Energiemanagement als Hebel.
  - Vermeidbarer Verbrauch bleibt ohne Analyse unsichtbar; Rausch liefert reale RLM-Daten.
- **Ziel der Studie:**
  - Erklärbare, übertragbare Anomalie-Pipeline mit automatisierten Handlungsempfehlungen.
- **Hypothese / Forschungsfrage (1 Satz, groß gesetzt, ~32–40 pt):**
  - „Ein Ensemble komplementärer Detektionsmethoden erkennt Lastgang-Anomalien
    zuverlässiger als jede Einzelmethode — und eine lokale LLM-Schicht überführt sie
    in konkrete Handlungsempfehlungen."
- **Visualisierung:** kleines Motiv-Icon (Strom/Gebäude) optional.
- **Wort-Budget:** ~100.

### Block 2 — Methode
- **Stichprobe:** 22 Baumärkte + 1 Sonderfall (Baumarkt_23, nur 2025), RLM-Lastgänge
  15-min, 2023–2026.
- **Studiendesign:** Train/Test-Split an 2025-01-01 *(kurz erwähnt, nicht ausgeführt)*.
- **Messinstrumente:** vier Anomalie-Methoden — **Z-Score** (Punkt-Outlier),
  **ARIMA** (Forecast-Abweichung), **Cluster-Distanz** (Segment-Form),
  **Autoencoder** (Rekonstruktionsfehler) — plus **LLM-Pipeline** (Qwen 2.5 7B,
  schema-erzwungene Empfehlung).
- **Visualisierung:** Methodik-Flowchart (eigene Skizze): RLM → STL/Features →
  4 Methoden-Stränge → Union-Ensemble → LLM-Empfehlung. Methoden in Projektfarben
  (`config/dashboard.yaml`: zscore `#1f77b4`, arima `#d62728`, cluster `#2ca02c`,
  autoencoder `#9467bd`).
- **Wort-Budget:** ~120.

---

## Spalte 2 (Mitte, ~250 mm) — Ergebnis-Block, zentrale Visualisierungen

### Block 3 — Ergebnis
- **Hypothesenprüfung / Hauptbefund:**
  - Vier Methoden **komplementär**: κ ≈ 0 über alle Paare (max 0,11) → disjunkte
    Anomalie-Mengen, **kein Einzelsieger** → Hypothese bestätigt, Empfehlung Union-Ensemble.
  - Precision **100 % über alle vier Methoden** auf den Top-Kandidaten (66 manuell bestätigt).
- **Erwartetes + überraschendes Ergebnis:**
  - Erwartet: Methoden disjunkt. Überraschend: Autoencoder nur ~20× langsamer als
    Cluster, aber **~20× schneller als ARIMA** *(als Stichpunkt, kein eigenes Diagramm)*.
- **Visualisierung 1:** `reports/figures/06_kappa_heatmap.png` (κ-Komplementarität).
- **Visualisierung 2:** `reports/figures/06_sweep_flag_rates.png` (Flag-Rate-Sweep,
  Sweet-Spot X = 0,25).
- **LLM-Pipeline-Statistik + echtes Beispiel:** 66/66 erfolgreich, 0 Schema-Fehler.
  Empfehlungs-Karte aus `reports/llm_recommendations/001.json` (Baumarkt_03, nachts):
  Last 72,6 kW vs. erwartet 8,0 kW (**+807 %**), Mehrkosten **31,35 €**; Ursache
  „HVAC-Nachtabsenkung nicht eingehalten", Schweregrad **hoch**, Konfidenz 0,85.
- **Optional:** Dashboard-Screenshot (`reports/dashboard_screenshots/`,
  Cost-First-Stakeholder-Ansicht) — sonst weglassen.
- **Wort-Budget:** ~150.

---

## Spalte 3 (rechts, ~250 mm) — HERVORGEHOBEN

### Block 4 — Schlussfolgerung + Ausblick
> **Visuelles Highlight (Müßig-Pflicht):** akzentuierter Hintergrund (z. B. `#F2F2F7`
> mit blauem Rand `#007AFF`, oder dezent `#007AFF` mit weißem Text), Schriftgröße
> ~20–25 % größer als Body, Font-Weight **700**, optional Pfeil/Trennlinie davor.

- **Interpretation / Kernaussage (groß):**
  - „Ein **Ensemble aus vier statistischen Methoden plus LLM-Pipeline** ermöglicht
    plausible Anomalie-Erkennung mit konkreten Handlungsempfehlungen — erklärbar und
    ohne pro-Standort-Training."
- **Praktische Implikationen:**
  - Energiemanagement: priorisierte, kostenbewertete Anomalien je Standort; Re-Thresholding
    über Schwellwert-Slider statt Neu-Inferenz.
  - Lokales LLM: datenschutzfreundlich, kein Cloud-Abfluss (Nachhaltigkeitsbezug, SDG 7/9).
- **Ausblick:**
  - Übertragbarkeit auf weitere Kategorien (Tankstellen, Büro, Handel) — architektonisch
    vorgesehen, als nächster Schritt zu prüfen.
- **Visualisierung:** keine Plots; Typo-/Akzent-Block, optional SDG-7/9-Icons.
- **Wort-Budget:** ~150.

---

## Footer (klein, dezent, ~25 mm)

### Block 5 — Referenzen
- **Nur die 1–2 zentralen methodischen Anker:**
  - Chandola et al. (2009) — Anomaly Detection: A Survey.
  - Cleveland et al. (1990) — STL-Dekomposition.
- Klein in der Ecke, dezent; vollständige Bibliographie im Paper (`paper/references.bib`).
- **Wort-Budget:** ~15.

---

## Wort-Budget gesamt

| Block | Wörter |
|---|---|
| 1 Einführung | ~100 |
| 2 Methode | ~120 |
| 3 Ergebnis | ~150 |
| 4 Schlussfolgerung + Ausblick (hervorgehoben) | ~150 |
| 5 Referenzen | ~15 |
| **Summe** | **~535** — typisch für A1 (Header ~25 zusätzlich) |

## Visuelle Verteilung

- Ziel **~60 % Visualisierung / ~40 % Text**:
  - Spalte 1: Methodik-Flowchart (+ optionales Motiv-Icon).
  - Spalte 2: κ-Heatmap · X-Sweep · LLM-Empfehlungs-Karte (· optional Dashboard-Shot).
  - Spalte 3: Akzent-/Typo-Block (Text-dominant, durch Hervorhebung visuell stark).

## Bewusst nicht aufs Poster (Müßig-Logik)

- „Schön zu wissen" → Vortrag/Paper, nicht Poster: HVAC-Default-Hypothese-Limitation,
  Wetterdaten-Limitation, AE-Pro-Site-Normierungs-Details, Hyperparameter-/Variantenstudie.
- „Gut zu wissen" → nur Stichpunkt, nicht ausgeführt: Train/Test-Split-Details,
  Inferenzkosten-Vergleich (eine Zeile im Ergebnis, kein eigenes Diagramm).

---

## Layout-Empfehlungen

- **Schriftgrößen** (lesbar aus ~1,5 m): Titel ≥ 60 pt, Section-Header ≥ 32 pt,
  Body ≥ 24 pt, Schlussfolgerung-Body ~30 pt (20–25 % größer), Footer/Referenzen ≥ 18 pt.
- **Farben** konsistent mit Dashboard (`config/dashboard.yaml`): Methodenfarben
  (zscore `#1f77b4`, arima `#d62728`, cluster `#2ca02c`, autoencoder `#9467bd`),
  Severity (hoch `#d62728`, mittel `#ff7f0e`, niedrig `#2ca02c`), Akzent `#007AFF`
  für den Schlussfolgerungs-Block.
- **Whitespace** großzügig — bei A1 wirken überfüllte Poster gedrungen.
- **THWS-Designvorgaben:** prüfen, ob Müßig/THWS eine offizielle Poster-Vorlage oder
  CD-Vorgaben (Logo, Farben, Schrift) stellt — falls ja, diese befolgen. *(User-Check)*
- Abbildungen mind. 1500 px breit, Achsen mit Einheit, eigene Plots „Eigene Darstellung".

## Müßig-Kriterien-Check

- **Logik des Aufbaus:** 5-Element-Struktur (Einführung → Methode → Ergebnis →
  Schlussfolgerung → Referenzen) erfüllt, Lesefluss links→rechts.
- **Originalität:** Cost-First-Stakeholder-Sicht im Ergebnis-Block, Ensemble-Argument als USP.
- **Visualisierung:** 2 Haupt-Plots (κ-Heatmap, X-Sweep) + 1 LLM-Empfehlungs-Karte, ~60 % visuell.
- **Nachvollziehbarkeit:** Problem → Methode → Ergebnis → Schlussfolgerung klar in dieser Reihenfolge.
- **Quellenangaben:** 1–2 zentrale Referenzen im Footer, Vollbeleg im Paper.

## Poster-Tools

- **Standard:** LaTeX mit `beamerposter` oder `tikzposter` (A1, `orientation=landscape`).
- **Alternative:** Affinity Publisher / Adobe InDesign.
- **Schnell:** PowerPoint mit A1-Seiteneinrichtung (84,1 × 59,4 cm) oder Canva-A1-Template.

---

## Offene User-Checks

- Finaler Titel des Papers/Posters.
- THWS-/Müßig-Poster-Vorlage (User klärt).
- Geeigneter Dashboard-Screenshot (sobald verfügbar; sonst Block-3-Option weglassen).
