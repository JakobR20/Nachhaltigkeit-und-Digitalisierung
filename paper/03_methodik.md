# 3 Methodik

> Wortbudget **~1000** (Kern). Ton: Plural, jede Designentscheidung kurz begründen.
> **Anker:** `reports/methodology.md` (lebendes Methodenkapitel), `docs/CLAUDE_patch_v4.md`,
> Tabelle `reports/tables/06_method_comparison.md`.

## 3.1 Datengrundlage (~150 W)

- **Quelle:** RLM-Lastgänge von Rausch Technology, **22+1 Baumärkte** (Baumarkt_23 als
  Sonderfall, s. 3.6), eine Excel-Datei je Standort.
- **Auflösung:** 15 min; Einheit **kW (Leistung)**, Konversion `energy_kwh = power_kw · 0,25`.
- **Zeitraum:** 2023-01-01 bis ca. 2026-03; ~105.120 Punkte/Standort.
- **Besonderheiten:** dynamische Header-Position, DST-Varianten (Herbst-Duplikate /
  Frühjahrs-Lücke), Europe/Berlin lokal. [Detail aus EDA übernehmen, knapp halten]
- **Externe Kontextdaten:** Wetter (Bright Sky/DWD) und Day-Ahead-Strompreis (Energy-Charts),
  monatsweise gecacht. Wetter standortgenau je PLZ-Centroid (eine DWD-Reihe pro Site).

## 3.2 Train/Test-Split (~50 W)

- **Zeitlicher Split** vor/nach **2025-01-01**: Train 2023–2024, Test ab 2025.
- Kein Leakage; exogene Kalender-Arrays (Feiertage) für Train und Forecast konsistent
  abgeleitet. [methodology.md, ARIMA-Abschnitt]

## 3.3 Methoden-Vergleichsdesign — vier Methoden (~350 W)

> Begründung der Auswahl: vier Methoden sollen **unterschiedliche Signalfamilien** erfassen,
> nicht dasselbe dreimal (methodology.md). Industriepartner empfahl Autoencoder; statt
> Autoritätsargument → empirischer Vergleich (v4 §1.1).

- **Signalfamilien:** Z-Score + ARIMA auf STL-**Residual** (Punkt-/Niveauabweichung);
  AE + Cluster auf dem **Rohsignal** (Form). Implikation für κ in Ergebnissen erwähnen.

### Z-Score auf STL-Residual (Baseline)
- STL (period=96, Tagesperiode auf 15-min-Basis) → Punkt-Outlier im Residuum, Schwelle 3,0 σ.
- Voll erklärbar, ~0 Inferenzkosten. Modul `models/baseline_zscore.py`. [@cleveland1990stl; @chandola2009anomaly]

### ARIMA pro Peer-Cluster (Haupt A)
- ARIMA auf saison-bereinigter Reihe (Trend+Remainder), **nicht** reines Remainder
  (sonst redundant zu Z-Score). `is_holiday` als SARIMAX-Exogen (empirisch: Anomalierate
  an Feiertagen ~2,3× erhöht). Ein Modell je Peer-Cluster (k=3), da pro-Zähler nicht skaliert.
  Modul `models/arima_clustered.py`. [@box2015time; @hyndman2021forecasting]

### Cluster-Distanz pro Segment (Haupt B)
- Distanzbasierte Diagnose-Schicht, methoden-agnostisch: kontinuierliche Distanz zum
  nächsten Cluster-Zentrum je Tageszeit-Segment (nachts/vormittag/mittag/nachmittag),
  Schwelle aus Train-Distanzen (99. Perzentil). Modul `models/clustering_segments.py`.
  [@aghabozorgi2015time]

### Autoencoder Dense+LSTM pro Kategorie (Haupt C)
- Eingang roher 24h-Lastgang (96 Slots), **pro-Site-StandardScaler** (fängt Form *und*
  site-internes Niveau, verfehlt bewusst Zwischen-Site-Magnitude). Rekonstruktionsfehler
  als Score. Modul `models/autoencoder.py`. [@malhotra2016lstm; @pang2021deep]
- **macOS-Recovery erwähnen** (TF 2.16 + Keras 2, `TF_USE_LEGACY_KERAS=1`): kurz als
  Reproduzierbarkeits-Hinweis, Details in methodology.md.

> Rolle des Clusterings (zwei getrennte Aufgaben): **Tagesprofil-Cluster** = Voraussetzung
> für ARIMA; **Segment-Cluster** = Diagnose für alle Methoden. [methodology.md „Rolle des
> Clusterings"; Abb. `04_silhouette_*` als Beleg]

### Aggregations-Schwelle X
- `threshold_pct` aggregiert Punkt-Flags auf Segment-Tag-Ebene; **X_default = 0,25**
  (begründet im Sweep, Kap. 4). [methodology.md „X-Wahl"]

## 3.4 Plausibilitäts-Annotation (~100 W)

- **66 Anomalie-Kandidaten** (Top-|score| je Methode, prioritäts-dedupliziert) manuell
  von Felix & Jakob gesichtet, drei Stufen (`plausibel_anomal` / `erklärbar` / `unklar`).
- Artefakte: `reports/annotation/annotation.csv`, `plot_{001..066}.png`.
- Zweck: methoden-spezifische Precision-Schätzung auf den stärksten Kandidaten (keine
  False-Negative-Bewertung — Budget-Limitation, Kap. 5). [methodology.md „Plausibilitäts-Validierung"]

## 3.5 LLM-Pipeline (~250 W)

- **Modell:** Qwen 2.5 7B lokal via Ollama (`temperature=0,2`, fester Seed), Output per
  **JSON-Schema-Grammatik erzwungen** + Pydantic-validiert. [@qwen2024technical; @willard2023efficient]
- **Prompt-Variantenwahl:** drei System-Prompts (V1 minimal / V2 few-shot / V3) qualitativ
  auf 5 bestätigten Test-Anomalien verglichen → **V2 (few-shot)** gewählt: erkennt Unterlast
  als Effizienzgewinn, kalibrierte Konfidenz 0,75–0,85, domänenspezifischer Kontext; V1
  disqualifiziert (defekter Output, überkonfident). [@brown2020language für Few-Shot-Konzept;
  Evidenz `reports/llm_evaluation/variant_comparison.md`]
- **Kontext-Builder** (`build_full_context`): reichert jede Anomalie mit **deterministisch
  berechneten** Fakten an — Lastgang (`value_kw`, `expected_kw` als 7-Wochen-Median,
  `diff_kw/pct`), Wetter (standortgenau je Site-PLZ), Strompreis (Day-Ahead, ct/kWh), **Mehrkosten
  im Code** (`diff_kw · dauer_h · preis`, methodenabhängige Dauer). Das LLM schätzt keine
  Zahlen. [methodology.md „Kontext-Builder (Phase 3)"; Samples `reports/llm_evaluation/full_context_samples.md`]
- **Produktionslauf (Phase 4):** über alle 66 `plausibel_anomal`-Anomalien; Output
  `reports/llm_recommendations.csv` + `{001..066}.json`. [Statistik in Kap. 4]
- **Qualitätssicherung:** Die generierten Empfehlungen wurden qualitativ auf Plausibilität
  geprüft (Domänen-Bezug, Konsistenz mit Anomalie-Typ, Umsetzbarkeit der Maßnahmen); keine
  systematische quantitative Quality-Skala. [Befund in Kap. 4.6, Limitation Kap. 5.3]

## 3.6 Bewertungsmetriken (~80 W)

- **Cohen's κ** (paarweise Methodenübereinstimmung). [@cohen1960coefficient]
- **Geschätzte Precision** auf Annotations-Stichprobe.
- **Flag-Rate** (Train/Test) und **Inferenzzeit** (Wall-Time fit/score) je Methode.
- **LLM:** Schema-Fehlerquote, Retries, Konfidenz-Verteilung, Schweregrad-Verteilung,
  später `quality_label` (Phase 5).

## 3.7 Sonderfall & Werkzeug (~20 W)

- **Baumarkt_23**: nur 2025-Daten, kein Trainingszeitraum → als Leakage-Sonderfall
  transparent ausweisen oder ausschließen (einheitlich für alle Methoden).
- **Dashboard** (Streamlit) als Visualisierungs-/Belegwerkzeug, nicht Prüfungsleistung.
  [Verweis, kein eigenes Kapitel]
