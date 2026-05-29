# Methodology (work in progress)

> Lebendes Methodenkapitel. Wird im Verlauf der Modellierungsphase gefüllt; die finale
> Methodenentscheidung fürs Dashboard wird hier nach dem Methodenvergleich (v4 §5
> Schritt 11+12) dokumentiert.

## Methodenvergleich (vier Methoden)

| Layer | Methode | Status |
|-------|---------|--------|
| Baseline | Z-Score auf STL-Residual | portiert (`models/baseline_zscore.py`) |
| Haupt A | ARIMA pro Peer-Cluster (auf STL-deseasonalized) | portiert (`models/arima_clustered.py`) |
| Haupt B | Cluster-Distanz pro Segment | portiert (`models/clustering_segments.py`) |
| Haupt C | Autoencoder (Dense + LSTM) pro Kategorie | portiert (`models/autoencoder.py`); macOS-Hang gelöst über TF 2.16 + Keras 2 (`TF_USE_LEGACY_KERAS=1`), s.u. |

Vergleichsmetriken: geschätzte Precision (manuelle Annotation ≈ 200 Punkte), Cohen's Kappa
(Methodenübereinstimmung), Inferenzzeit pro Standort, qualitative Erklärbarkeit.

## Rolle des Clusterings (zwei klar getrennte Aufgaben)

Das Clustering hat **zwei unterschiedliche Aufgaben** mit **unterschiedlichen Objekten** –
diese Trennung ist bewusst, damit nicht der Eindruck „wozu Clustering, wenn der Autoencoder
es nicht braucht?" entsteht:

- **Tagesprofil-Clustering → ausschließlich Voraussetzung für ARIMA.** ARIMA pro Einzelzähler
  skaliert nicht; daher werden Standorte über ihre mittleren Tagesprofile in **Peer-Gruppen**
  (k=3, fachlich) zusammengefasst und **ein ARIMA je Gruppe** trainiert. Der **Autoencoder**
  braucht das **nicht** – er wird **pro Kategorie** trainiert (v4 §1.1). Modul:
  `models/clustering_daily.py`.
- **Segment-Clustering (distanzbasiert) → Diagnose-Schicht für ALLE Methoden.** Es beantwortet
  methoden-agnostisch „ist dieser Segment-Tag untypisch und welche Tageszeit?" – als
  **kontinuierliche Distanz zum nächsten Cluster-Zentrum** (nicht als Label), je Segment
  getrennt standardisiert, Schwelle aus den Train-min-Distanzen (Default 99. Perzentil).
  Weil die Distanz das Signal trägt, ist die Clusterzahl niedrig-sensitiv (Silhouette-Tendenz
  zu k=2 unkritisch); k=3 je Segment (Mittag k=4, silhouette-getrieben). Modul:
  `models/clustering_segments.py`. Der Distanz-Score ist kontinuierlich und damit im
  Methodenvergleich (Schritt 11) direkt neben Z-Score und ARIMA-Residuum stellbar.

## ARIMA: Eingang (Trend+Remainder) und Feiertage

**Warum ARIMA auf der saison-bereinigten Reihe (Trend + Remainder), nicht auf dem reinen
Remainder?** Wenn die STL ihre Arbeit tut, ist das Remainder annähernd **weißes Rauschen** –
ein ARIMA darauf wäre **nahezu redundant zum Z-Score** (beide messen dann nur die Streuung
des Restrauschens). Auf **Trend + Remainder** modelliert ARIMA dagegen echte **Restdynamik
und Trend** und liefert ein sinnvolles Prädiktionsintervall. Das ist ein bewusstes
Paper-Argument: Die drei Methoden sollen **unterschiedliche Signale** erfassen
(Z-Score = Punktausreißer im Remainder; ARIMA = Abweichung von der prognostizierten
Dynamik; Autoencoder = Rekonstruktionsfehler des Tagesmusters), nicht dasselbe dreimal.
Saison wird über STL (period=96) entfernt, **nicht** über `s=96` in SARIMAX (bei 15-min zu
langsam).

**Feiertage als Exogen – empirisch geprüft (kein Annehmen).** Auf dem frischen
96-Residuum ist die Anomalierate an (bayerischen) Feiertagen im Mittel **~2,3× erhöht**
(9,97 % vs. 4,35 %), bei großen Standorten stark (Baumarkt_06: 23,6 % vs. 6,4 %), bei
kleinen kaum. STL absorbiert die **irregulären** Feiertage also **nicht** → `is_holiday`
als SARIMAX-Exogen ist begründet. Das exogene Array muss für **Train und Forecast
konsistent** aus demselben Kalender abgeleitet werden (kein Leakage, gleiche Länge/Index).

**Notiz fürs Diagnose-Design (jetzt nur festhalten, nicht lösen):** Feiertage sind
**erwartbare Anomalien** (Klasse 2 der Operationalisierung), keine Schadschöpfung.
`is_holiday` gehört perspektivisch generell als **Kontext-Feature in die Diagnose-Schicht**,
damit nicht jede Methode Feiertage als Fehlalarm meldet – methoden-übergreifend statt je
Methode einzeln.

## Autoencoder: Eingangssignal und Normierung (bewusste Designentscheidung)

- **Eingang = roher 24h-Lastgang** (Variante A), **nicht** das STL-Residual. Damit lernt der
  AE die Saisonalität selbst und misst Abweichungen vom typischen Tagesmuster. Konsequenz für
  die Signal-Familien: **AE + Cluster arbeiten auf dem Rohsignal (Form), Z-Score + ARIMA auf
  dem STL-Residual (Punkt-/Niveauabweichung)**. Gleiche Eingangssignale sind in Schritt 11
  erwartbar höher korreliert — die κ-Werte sind entsprechend zu lesen.
- **Normierung pro Site** (StandardScaler, auf Train gefittet) — bewusst **nicht** pro Fenster:
  - **Fängt Form *und* site-internes Niveau.** Ein Tag mit normaler Form, aber durchgehend
    erhöhtem Niveau (z. B. Nacht-Basislast ~18–22 statt ~6 kW = durchlaufende Heizung) bleibt
    im Standard-Raum erhöht → hoher Rekonstruktionsfehler → wird geflaggt. **Genau diese
    Niveau-Verschwendung soll das Projekt finden** — pro-Fenster-Normierung (form-only) würde
    sie glattrekonstruieren und **verfehlen**.
  - **Was der AE NICHT fängt:** reine **Zwischen-Site-Magnitude** (ist wegnormiert) — gewollt,
    sonst dominiert die größte Site das eine Kategorie-Modell.
- **κ-Erwartung (revidiert):** Der AE ist durch Form + site-internes Niveau ein **breiterer**
  Detektor und damit **moderat zu ALLEN** anderen Methoden korreliert — eine **Brücke**
  zwischen der Form-Familie (Cluster) und der Niveau-/Punkt-Familie (Z-Score, ARIMA), **nicht**
  speziell hoch nur zu Cluster. (Die frühere Erwartung κ(AE,Cluster) > κ(AE,Z-Score) war an die
  form-only-Normierung gekoppelt und ist verworfen.)
- **Struktur-Notiz:** v4 §4 nennt zwei Dateien (`autoencoder_dense.py`, `autoencoder_lstm.py`);
  bewusst zu **einer** Klasse `models/autoencoder.py` mit `variant`-Flag zusammengefasst (weniger
  Duplikat). v4 ist Plan, kein Vertrag.

## Autoencoder: Stage-A-Befund + macOS-Recovery (2026-05-29 / 2026-05-30)

**Stage-A-Befund (29.05.2026):** Unter **TF 2.21 + Keras 3.14** hing
`tf.keras.Model.fit()` auf der Entwicklungs-macOS-Box reproduzierbar in Epoch 1,
sobald die Trainingsdaten realistische Größenordnung erreichten (Stage A: 2
Baumärkte, 1092 Tagesfenster × 96 Slots, float32, ~750 MB RSS). Der Hang trat
auf

- mit und ohne `validation_split`,
- mit und ohne Callbacks (insbesondere `EarlyStopping`),
- in **pytest** wie in einem **reinen Python-Skript** (`/tmp/stage_a_minfit.py`),
- bei `epochs=2` schon im allerersten Epoch (kein Fortschritt nach „Epoch 1/2"),
- 0 % CPU, nur per `SIGKILL` beendbar.

Abgrenzung damals: derselbe `AutoencoderDetector` lief auf dem synthetischen
Mini-Datensatz (`/tmp/ae_diag.py`, 8 Fenster, `val=0`) in <0,3 s sauber durch.
Der Hang war **scale-bound** und (wie sich am Folgetag bestätigte)
**Keras-3-spezifisch** auf macOS.

**macOS-Recovery (30.05.2026):** Stufe A der gestaffelten Recovery
(TF-Version-Downgrade) löste den Hang vollständig. Pin:

- `tensorflow==2.16.2` (statt 2.21)
- `tf-keras==2.16.0` (Keras-2-Maintenance-Paket)
- `TF_USE_LEGACY_KERAS=1` auf Modulebene in `models/autoencoder.py` gesetzt,
  bevor `tensorflow` importiert wird — leitet `tf.keras` auf `tf_keras` um.

**Empirische Belege:**

- **Stage A** (2 Sites, 1092 Fenster, epochs=30): `setup` in **49,6 s** (statt
  Hang); threshold = 1,5838.
- **Stage B v2** (Anomalie-Injektion auf Baumarkt_03, 5 Werktage gemittelt gegen
  Test-Slice-Median):
  - Niveau × 2,0:  mittlere Ratio **16,5** (Target ≥ 2,0).
  - Form invertiert: mittlere Ratio **38,2** — deutlich höher als Niveau,
    bestätigt die methodology-These „per-site StandardScaler behält das Niveau,
    der AE ist primär sensitiv für Form-Abweichungen".
- **Stage C** (Vollauf 22 Baumärkte, `run_autoencoder(write=True)`): **68,2 s**,
  2,19 M Score-Zeilen ins `data/processed/anomaly_scores.parquet`, gesamte
  Test-Flag-Rate **1,12 %**, pro-Site-Raten plausibel verteilt (0,0 % .. 5,99 %,
  Median ≈ 1 %).
- **Tests** (`tests/test_autoencoder.py`): die vier zuvor mit
  `@pytest.mark.skip` markierten fit-basierten Tests laufen jetzt grün
  (5 passed in 8,66 s, inkl. LSTM-Variante und save/load-Roundtrip).

**Konsequenzen für die Auswertung:**

- **Methodenvergleich wird auf vier Methoden erweitert:** Z-Score, ARIMA,
  Cluster-Distanz **und** Autoencoder. Die AE-Scores sind nativ
  `granularity="point"` und passen in dasselbe parquet-Schema wie Z-Score und
  ARIMA. Die Schritt-11-Tabelle und das Notebook 06 müssen entsprechend
  erweitert werden (separate Folge-Iteration auf dem `method-comparison`-
  Branch, da der Annotations- und Methodenvergleich dort bereits abgeschlossen
  war).
- **Modul-Status:** `models/autoencoder.py` und Driver
  `evaluation/scoring.run_autoencoder` sind weiter im Code und jetzt auf macOS
  voll lauffähig. CI/Linux profitieren unverändert vom selben Pin.
- **Paper-Diskussion:** „Welche Methoden gewinnen?" wird auf den drei portierten Methoden
  beantwortet; der AE wird als **methodologisch verfolgter, lokal nicht durchführbarer**
  Pfad im Limitations-Abschnitt offen ausgewiesen — ehrlicher als unter Druck auf eine
  fragile Variante (kürzerer Train-Slice, reduzierte Epochen) umzubiegen.
- **κ-Erwartungs-Diskussion (oben) bleibt gültig** als methodische Verortung, aber nicht
  als empirisch zu validierende Hypothese in diesem Lauf.

## STL-Periode (96 vs. 168 vs. 672)

Die STL-Saisonperiode ist eine **methodische Entscheidung**, kein Detail. Sie muss zur
Sampling-Auflösung passen:

- **`period = 96` (Default):** Tagesperiode auf **15-min**-Basis (24 h × 4). Das ist die
  korrekte Dimensionierung für unsere RLM-Daten, die nativ in 15-min vorliegen.
- **`period = 168`** war im **alten** Code gesetzt, galt aber für auf **Stunden**
  resampelte Daten (7 × 24 = Wochenperiode auf 1-h-Basis). Für die jetzige 15-min-Pipeline
  ist 168 **falsch dimensioniert** (entspräche nur 42 h) und wird nicht verwendet.
- **`period = 672` (optional):** Wochenperiode auf 15-min-Basis (7 × 96). Wird als
  zusätzliche Variante für einen **STL-Robustvergleich** in der Feature-Phase geführt: Tages-
  vs. Wochensaison, Einfluss auf das Residuum (und damit auf die Anomalie-Rate).

Beide Perioden (96, 672) sind methodisch begründet; die Tagesperiode 96 ist der Default,
672 dient der Sensitivitätsprüfung.

## Offene Sensitivitäts-/Limitationsdiskussionen

- **CO₂-Intensität:** Default 380 g/kWh (Jahresmittel DE) vs. stündliche Variante via
  Energy-Charts `/public_power`. Sensitivität der abgeleiteten CO₂-Aussagen hier diskutieren.
- **Würzburg-Default:** Solange Postleitzahlen fehlen, werden alle Standorte mit Würzburger
  Koordinaten/Bundesland (BY) bewettert. Sensitivität (regionale Wetterunterschiede,
  Feiertags-Bundesland) als Limitation diskutieren.
- **Übertragbarkeit:** Innerhalb-Kategorie-Generalisierung (trainieren auf N Baumärkten,
  anwenden auf einen weiteren) statt Cross-Category-Transfer (v4 §1.3).
- **Schwelle X + Ensemble vs. Sieger (Schritt 11):** beide ursprünglich offenen Fragen
  sind durch den Sweep + die Plausibilitäts-Annotation empirisch beantwortet — siehe
  eigenen Abschnitt „Methodenvergleich (Schritt 11) — Befund" unten. Die hier zuvor
  zitierten Zahlen (ARIMA ~30 %, Z-Score ~14 % bei „any"; κ ≈ 0,45 zscore↔arima) galten
  für `X=0` (any-Aggregation) und sind im Schritt-11-Abschnitt mit dem gewählten
  `X=0,25` aktualisiert.

## Methodenvergleich (Schritt 11) — Befund

Sweep-Lauf am 30.05.2026 auf dem aktuellen `data/processed/anomaly_scores.parquet`
über die drei portierten Methoden (`zscore_stl`, `arima`, `cluster_segment`;
Baumarkt_23 ausgeschlossen). Code: `evaluation/method_comparison.py`. Notebook:
`notebooks/06_method_comparison.ipynb`. Outputs:
`reports/tables/06_method_comparison.md`, `reports/figures/06_*`.

### Cluster-Anker

Cluster-Distanz ist nativ Segment-Tag und damit der Anker für die X-Wahl der
Punkt-Methoden. Test-Flag-Rate (2025+) im aktuellen Parquet: **0,64 %** (der
frühere Wert 0,86 % aus dem Smoke-Lauf war ein Zwischenstand).

### X-Wahl (Aggregations-Schwelle der Segment-Tag-Hochaggregation)

Sweep über `threshold_pct ∈ {0,0, 0,10, 0,25, 0,50, 0,75}`. Bei `X=0`
(any-Aggregation) bestätigt sich der frühere Smoke-Befund: ARIMA 28,6 %,
Z-Score 13,1 % — methodisch nicht haltbar.

**Eigener Befund:** Es gibt **keinen einzigen `X`**, der `zscore_stl` und
`arima` gleichzeitig in 0,5×..2× des Cluster-Ankers bringt. Z-Score
produziert pro Segment systematisch **breitere** Punkt-Anomalien als ARIMA.
Konkret bei der Test-Flag-Rate:

- `X = 0,25`: ARIMA 1,05 % (Ratio 1,64 zum Anker ✓), Z-Score 3,90 % (Ratio 6,1).
- `X = 0,75`: Z-Score 0,63 % (Ratio 0,99 ✓), ARIMA 0,00 % (ARIMA verschwindet).

Diese Asymmetrie ist ein **eigenständiger qualitativer Befund**, kein Bug
der X-Wahl. Sie spiegelt wider, wie die Methoden Anomalien räumlich-zeitlich
verteilen: Z-Score „streut" Flags über die gesamte Anomalie-Periode, ARIMA
markiert nur die scharfen Forecast-Sprünge.

**Entscheidung: `X_default = 0,25`.** ARIMA-Sichtbarkeit ist wichtiger als
rein numerische Anker-Nähe; `X = 0,75` würde ARIMA effektiv aus dem
Vergleich nehmen. In `config/config.yaml` unter
`comparison.aggregation_threshold_pct: 0.25` abgelegt; das Notebook nutzt
diesen Override automatisch (`load_default_threshold_pct`).

### Komplementarität (κ)

Bei `X = 0,25` sind **alle paarweisen κ ≤ 0,08** (zscore↔arima 0,08,
zscore↔cluster −0,01, arima↔cluster 0,02). Die in der älteren
Limitationsdiskussion zitierten Werte (κ ≈ 0,45 zscore↔arima, κ ≈ 0
cluster↔beide) galten für das alte `flag.any()` (`X = 0`). Mit der
Anteils-Schwelle löst sich die scheinbare Z-Score/ARIMA-Überlappung auf:
**alle drei Methoden detektieren weitgehend disjunkte Anomalie-Mengen**.
Die Komplementaritäts-These wird **verstärkt**, nicht widersprochen. Die
κ-Heatmaps über die Sweep-Werte (`reports/figures/06_kappa_heatmap.png`)
zeigen, dass die Disjunktheit über alle X ≥ 0,25 stabil bleibt.

### Inferenzkosten

Mikrobenchmark auf 5 soliden Sites (`reports/tables/06_method_comparison.md`):

| Methode | fit | score |
|---|---|---|
| zscore_stl | ~2 ms | ~0,3 ms |
| cluster_segment | 94 ms | 8 ms |
| **arima** | **93,2 s** | **47,2 s** |

ARIMA dominiert — hochgerechnet auf 22 Baumärkte **≈ 10 min je Vollauf**.
**Konsequenz für die Dashboard-Architektur:** ARIMA-Scores müssen aus dem
vor-berechneten `anomaly_scores.parquet` eingelesen werden — **kein
On-the-fly-Recompute** bei Threshold-Slider oder Methoden-Toggle. Z-Score
und Cluster-Distanz können interaktiv neu berechnet werden, falls
Hyperparameter-Slider eingeplant sind. Diese Trennung gehört explizit ins
Dashboard-Kapitel.

### Plausibilitäts-Validierung (Felix & Jakob, 30.05.2026)

Die Plausibilitäts-Stichprobe (`reports/annotation/`, 57 Top-Kandidaten je
Methode nach Prioritäts-Dedup) wurde am 30.05.2026 durchgesichtet. Befund:
**alle drei Methoden lieferten in ihren jeweiligen Top-Kandidaten Anomalien
mit hoher Plausibilität** (ungewöhnliche Verbrauchssignatur, kein
offensichtlicher Erklärungsgrund). Einzelne Kandidaten wurden manuell als
„unklar" markiert.

**Methodische Konsequenz:** Die Plausibilitäts-Validierung trennt die
Methoden auf dieser Stichprobe nicht — alle Methoden landen nahe 100 %
Precision auf ihren Top-|score|-Kandidaten. Der Methodenvergleich
verschiebt sich damit von „welche Methode hat die höhere Precision?" auf
**κ-Komplementarität und Inferenzkosten** als Auswahlkriterien. Das ist
methodisch nicht schwächer, sondern ein anderer Erkenntniswert: wir
messen, ob die Methoden komplementär sind, nicht ob eine eine andere
dominiert.

### Strategie-Empfehlung (Sieger vs. Ensemble)

`recommend_strategy` arbeitet mit **absoluten Schwellen** (siehe
Docstring): eine Methode hat Sieger-Status nur bei
`precision ≥ 0,90 UND max(κ vs jede andere Methode) ≤ 0,40`. Erfüllen
mehrere Methoden beide → **Ensemble (Union)**: die gemeinsam niedrige κ
beweist disjunkte Anomalie-Mengen; ein Ensemble summiert komplementäres
statt redundantes Wissen.

Mit den Schritt-11-Zahlen (Precision aller drei Methoden nahe 100 % auf
der Plausibilitäts-Stichprobe, alle paarweisen κ ≤ 0,08) **erfüllen alle
drei Methoden** die Sieger-Schwelle. Die Empfehlung lautet damit
**Ensemble (Union)** als Default für das Rausch-Dashboard.

- **Union** (sensitiv): Flag, wenn ≥ 1 Methode flaggt — niedrige
  False-Negative-Rate; richtige Default-Wahl für ein Dashboard, das je
  Flag einen Review zulässt.
- **Voting / Mehrheit** (konservativ): Flag, wenn ≥ 2 von 3 flaggen —
  höhere Precision pro Flag; geeignet für automatisches Pflicht-Reporting
  ohne manuellen Review.

Default: **Union**. Wahl Union vs. Voting hängt vom Dashboard-Workflow ab;
beide werden im Ergebnis dokumentiert.

## Datenqualität (Stand-/Sonderfälle)

- **Baumarkt_23 – nur 2025-Daten (Leakage-Sonderfall):** Diese Site beginnt erst 2025 und
  hat damit **keinen** Trainingszeitraum (2023–2024). Im Smoke-Lauf greift der ARIMA-Fallback
  „Fit auf voller Site-Reihe" — das ist für diese eine Site faktisch **Train-auf-Testzeitraum**
  (Leakage). **Für die finale Auswertung NICHT stillschweigend mitlaufen lassen:** entweder
  **ganz ausschließen** (zu wenig Historie, empfohlen) oder **transparent als Sonderfall**
  ausweisen. Entscheidung gilt einheitlich für alle Methoden (inkl. Autoencoder-Train/Test).
