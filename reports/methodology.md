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
- **Empirisch bestätigt (Stage B, 30.05.2026):** AE detektiert Form-Anomalien stärker als
  Niveau-Anomalien aufgrund der Pro-Site-Normierung — Form-Inversion liefert eine ~2,3× höhere
  Rekonstruktionsfehler-Ratio als Niveau-Verdopplung (38,2 vs. 16,5, gemittelt über 5 Werktage
  auf Baumarkt_03). Konsistent mit der oben begründeten Designentscheidung; siehe Abschnitt
  „Autoencoder: Stage-A-Befund + macOS-Recovery" für Mess-Details.

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

## Methodenvergleich (Schritt 11) — Befund (vier Methoden)

Sweep-Lauf erstmals am 30.05.2026 (drei Methoden) und reproduziert am 31.05.2026
mit der vierten Methode (`autoencoder`, nach macOS-Recovery), beide auf dem
aktuellen `data/processed/anomaly_scores.parquet`. Code:
`evaluation/method_comparison.py`. Notebook: `notebooks/06_method_comparison.ipynb`.
Outputs: `reports/tables/06_method_comparison.md`, `reports/figures/06_*.png`.

### Cluster-Anker

Cluster-Distanz ist nativ Segment-Tag und damit der Anker für die X-Wahl der
Punkt-Methoden. Test-Flag-Rate (2025+) im aktuellen Parquet: **0,64 %**.

### X-Wahl (Aggregations-Schwelle)

Sweep über `threshold_pct ∈ {0,0, 0,10, 0,25, 0,50, 0,75}`. Bei `X=0`
(any-Aggregation) bestätigt sich der frühere Smoke-Befund: ARIMA 28,6 %,
Z-Score 13,1 % — methodisch nicht haltbar.

**Eigener Befund (drei Punkt-Methoden, drei Profile):** Es gibt **keinen
einzigen `X`**, der alle drei Punkt-Methoden gleichzeitig in 0,5×..2× des
Cluster-Ankers bringt. Z-Score produziert pro Segment systematisch **breitere**
Punkt-Anomalien als ARIMA und AE. Konkret bei `X = 0,25` (Test-Flag-Rate):

| Methode | Flag-Rate Test | Ratio zum Anker (0,64 %) |
|---|---|---|
| `cluster_segment` | 0,64 % | 1,00 (Anker) |
| `arima` | 1,05 % | 1,64 ✓ im 0,5×..2×-Band |
| `autoencoder` | 1,21 % | 1,89 ✓ im Band |
| `zscore_stl` | 3,90 % | 6,1 (außerhalb) |

**Entscheidung: `X_default = 0,25`.** Zwei der drei Punkt-Methoden (ARIMA, AE)
landen sauber im Band; Z-Score bleibt aufgebläht und wird als eigenständiger
Befund ausgewiesen („Z-Score streut Flags breiter über die Anomalie-Periode als
ARIMA und AE — methodisch interessant, kein X-Wahl-Fehler"). `X = 0,75` würde
ARIMA auf 0 % drücken und damit aus dem Vergleich nehmen — nicht akzeptabel.
In `config/config.yaml` unter `comparison.aggregation_threshold_pct: 0.25`
abgelegt; das Notebook nutzt den Override über `load_default_threshold_pct`.

### Komplementarität (κ, 6 Paare bei X = 0,25)

| | `zscore_stl` | `arima` | `cluster_segment` |
|---|---|---|---|
| `autoencoder` | 0,03 | **0,11** | 0,03 |
| `cluster_segment` | −0,01 | 0,02 | — |
| `arima` | 0,08 | — | — |

Höchster Wert **κ(arima, autoencoder) = 0,11** — methodisch erklärbar: beide
Methoden reagieren auf abrupte Abweichungen vom erwarteten Verlauf (ARIMA
Forecast-Residuum, AE Rekonstruktionsfehler), daher partielle methodische
Verwandtschaft. Trotzdem klar komplementär: **alle sechs Paare liegen deutlich
unter der 0,40-Schwelle**.
Die alten 3-Methoden-κ ≤ 0,08 bleiben unverändert; AE addiert eine neue,
schwach mit ARIMA korrelierte Signal-Dimension. Die κ-Heatmaps über den Sweep
(`reports/figures/06_kappa_heatmap.png`) zeigen Disjunktheit über alle
X ≥ 0,25 stabil. Die in der älteren Limitationsdiskussion zitierten Werte
(κ ≈ 0,45 zscore↔arima, κ ≈ 0 cluster↔beide) galten für das alte
`flag.any()` (`X = 0`) und sind hier mit der Anteils-Schwelle obsolet.

### Inferenzkosten (Mikrobenchmark, 5 Sites)

| Methode | fit | score |
|---|---|---|
| `zscore_stl` | ~2 ms | ~0,3 ms |
| `cluster_segment` | 1,4 s | 8 ms |
| **`autoencoder`** | **5,2 s** | **3,2 s** |
| **`arima`** | **118,4 s** | **50,1 s** |

**Überraschung mit AE — Paper-relevanter Befund:** Der Autoencoder ist nur
Faktor ≈ 20 langsamer als Cluster-Distanz und etwa **20× schneller als
ARIMA**. Hochgerechnet entspricht ein Vollauf auf 22 Baumärkten **~22 s** für
AE versus **~10 min** für ARIMA. Das relativiert die übliche „Deep-Methoden
sind teuer"-Intuition: in dieser Setup-Größe (96-Slot-Tagesfenster, Dense-AE
mit Hidden 32 / Latent 8) ist der Autoencoder eine **vollständig interaktive**
Methode, und ARIMA wird zum allein dominanten Kostenfaktor. Gehört in die
Paper-Diskussion (Methoden-Charakteristik) und ins Dashboard-Kapitel:
**Nur ARIMA** muss aus dem vor-berechneten `anomaly_scores.parquet`
eingelesen werden; Z-Score, Cluster und auch AE können bei
Hyperparameter-Slidern on-the-fly neu laufen, ohne dass die Interaktivität
leidet.

### AE-Drift-Sensitivität (Train vs. Test)

Im Vergleich der vier Methoden ist **AE die einzige mit Test-Flag-Rate > Train**
(AE 1,21 % Test vs. 0,89 % Train; Ratio 1,36). ARIMA bleibt fast konstant
(1,05 / 1,03 ≈ 1,02), Cluster und Z-Score sinken vom Train zum Test
(0,64 / 1,01 ≈ 0,63 bzw. 3,90 / 5,06 ≈ 0,77). Lesart: **AE zeigt eine
Site-Verhaltensdrift zwischen 2023–24 und 2025**, die die anderen Methoden
mehr oder weniger glattbügeln. Die Pro-Site-StandardScaler-Normierung
(Designentscheidung Schritt 9) verstärkt diese Drift-Sensitivität, weil das
site-interne Niveau bewusst erhalten bleibt — ein wandernder Mittelwert über
die Jahre wird sichtbar. Methodisch konsistent mit dem Stage-B-Befund
„AE primär form-sensitiv, aber das Niveau bleibt im Standard-Raum erhalten".

### Plausibilitäts-Validierung (Felix & Jakob)

**Stand 30.05.2026 (drei Methoden):** Die ursprüngliche Plausibilitäts-
Stichprobe (57 Top-Kandidaten je Z-Score/ARIMA/Cluster nach Prioritäts-Dedup,
`reports/annotation/`) wurde durchgesichtet — **alle 57 als plausibel anomal
bestätigt**, keine `erklärbar`- oder `unklar`-Markierung. Empirische
Precision: arima 17/17, cluster_segment 20/20, zscore_stl 20/20 — alle
**100 %**.

**Stand 01.06.2026 (AE vollständig gelabelt, Commit 17a0516):** Nach AE-Recovery
wurden **9 zusätzliche AE-only-Kandidaten** an die Annotation angehängt
(`nr 58..66`; 11 weitere AE-Top-Treffer fielen als `(site, timestamp)`-Duplikate
auf die höher-priorisierten Methoden und sind dort als `also_flagged_by`
markiert). Diese 9 sind inzwischen von beiden Reviewern gesichtet und **alle als
`plausibel_anomal` bestätigt** — die Annotation umfasst damit alle 66 Kandidaten
vollständig. **AE-Precision = 9/9 = 100 %**, in derselben Größenordnung wie die
anderen drei Methoden (arima 17/17, cluster_segment 20/20, zscore_stl 20/20).

**Methodische Konsequenz** (unverändert mit AE): Die Plausibilitäts-
Validierung trennt die Methoden auf dieser Stichprobe nicht — sie zeigt, dass
jede Methode auf ihren Top-Kandidaten plausible Anomalien liefert. Der
Methodenvergleich konzentriert sich damit auf **κ-Komplementarität und
Inferenzkosten** als Auswahlkriterien. *Limitierung*: die Stichprobe ist
methodenspezifisch (Top-|score| je Methode) und prüft Precision auf den
*stärksten* Kandidaten, nicht in der Breite — eine Bewertung der
False-Negative-Rate war im Annotationsbudget nicht vorgesehen und gehört in
eine spätere Iteration.

### Strategie-Empfehlung (Sieger vs. Ensemble)

`recommend_strategy` arbeitet mit **absoluten Schwellen** (siehe Docstring):
eine Methode hat Sieger-Status nur bei
`precision ≥ 0,90 UND max(κ vs jede andere Methode) ≤ 0,40`. Erfüllen
mehrere Methoden beide → **Ensemble (Union)**: die gemeinsam niedrige κ
beweist disjunkte Anomalie-Mengen; ein Ensemble summiert komplementäres statt
redundantes Wissen.

**Aktueller Stand (alle vier Methoden gelabelt):** vier Qualifier
(arima, cluster_segment, zscore_stl, autoencoder; alle Precision = 100 % UND
max κ = 0,11 ≤ 0,40). Der unten zitierte `recommend_strategy`-Output stammt aus
dem Lauf **vor** dem AE-Labeling (drei qualifizierende Methoden); mit der nun
vollständigen Annotation qualifiziert AE als vierte Methode, die Empfehlung
(Ensemble/Union) bleibt unverändert:

```
strategy = ensemble
label    = union
rationale = 3 Methoden erfüllen das Sieger-Kriterium
           (arima, cluster_segment, zscore_stl); ihre paarweise κ ≤ 0,40
           zeigt, dass sie disjunkte Anomalie-Mengen detektieren.
           Union summiert komplementäres Wissen — Default-Ensemble
           für das Dashboard.
```

**Finale Lage (bestätigt nach AE-Labeling):** κ(AE, andere) ≤ 0,11 und
AE-Precision 100 % — AE qualifiziert als **vierte Methode**. Empfehlung bleibt
**Ensemble (Union)**, jetzt über vier statt drei Methoden — das Dashboard
kombiniert vier weitgehend disjunkte Signal-Familien.

- **Union** (sensitiv): Flag, wenn ≥ 1 Methode flaggt — niedrige
  False-Negative-Rate; Default-Wahl für ein Dashboard, das je Flag einen
  Review zulässt.
- **Voting / Mehrheit** (konservativ): Flag, wenn ≥ 2 von 4 flaggen — höhere
  Precision pro Flag; geeignet für automatisches Pflicht-Reporting ohne
  manuellen Review. *Nicht* die Default-Wahl bei `κ ≈ 0`, weil dann praktisch
  nie 2 Methoden gleichzeitig auf demselben `(site, date, segment)` flaggen
  — die konservative Variante würde fast leer laufen.

Default: **Union**. Wahl Union vs. Voting hängt vom Dashboard-Workflow ab.

## Datenqualität (Stand-/Sonderfälle)

- **Baumarkt_23 – nur 2025-Daten (Leakage-Sonderfall):** Diese Site beginnt erst 2025 und
  hat damit **keinen** Trainingszeitraum (2023–2024). Im Smoke-Lauf greift der ARIMA-Fallback
  „Fit auf voller Site-Reihe" — das ist für diese eine Site faktisch **Train-auf-Testzeitraum**
  (Leakage). **Für die finale Auswertung NICHT stillschweigend mitlaufen lassen:** entweder
  **ganz ausschließen** (zu wenig Historie, empfohlen) oder **transparent als Sonderfall**
  ausweisen. Entscheidung gilt einheitlich für alle Methoden (inkl. Autoencoder-Train/Test).

## LLM-Handlungsempfehlung: Prompt-Variantenwahl (Phase 2)

Lokales LLM `qwen2.5:7b` (Ollama, `temperature=0.2`, fester Seed), Output strukturell
per JSON-Schema-Grammatik erzwungen und anschließend per Pydantic validiert
(`confidence`-Reskalierung 0–100 → 0–1, String-Truncation). Drei System-Prompt-Varianten
wurden qualitativ auf 5 bestätigten Test-Anomalien verglichen (je eine pro Methode
zscore_stl/arima/cluster_segment/autoencoder plus eine Nicht-AE-Quersicht, Auswahl mit
Seed 42). **Gewählt: V2 (few-shot).** Begründung:

1. **Unterlast-Fall korrekt klassifiziert.** Bei der einzigen milden Anomalie (nr 43,
   −12 % gegenüber Erwartung) erkennt nur V2 die Minderlast als möglichen Effizienzgewinn
   statt als Defekt — methodisch wichtig für Anomalie-Plausibilität im Produktivbetrieb.
2. **Kalibrierte Konfidenz.** V2 liefert `confidence` im Band 0,75–0,85 und differenziert
   zwischen klar anomalen und ambivalenten Fällen — relevant für die Glaubwürdigkeit der
   Dashboard-Ausgabe.
3. **Domänenspezifischer Kontext.** V2 nutzt baumarktspezifische Verbraucher (Kühlung
   Gartencenter/Getränke, Anlieferung, Kundenfrequenz) statt generischer Formulierungen.
4. **V1 disqualifiziert.** V1 (minimal) erzeugte bei nr 19 einen defekten Output
   (abgeschnittene und duplizierte Empfehlungen, 1 von 5 Fällen = 20 % Fehlerrate) und war
   durchgehend überkonfident (0,92–0,95).

Produktions-Prompt festgeschrieben als `SYSTEM_PROMPT_PRODUCTION` in
`src/rausch_energy_anomaly/recommendations/prompts.py`. Evidenz (alle 15 Outputs,
Kontext-Prompts, Laufzeiten): `reports/llm_evaluation/variant_comparison.md`.

## LLM-Handlungsempfehlung: Kontext-Builder (Phase 3)

`build_full_context()` in `src/rausch_energy_anomaly/recommendations/context.py`
reichert jede Anomalie mit deterministisch berechneten Fakten an, die dem LLM als
gegeben übergeben werden (das Modell schätzt keine Zahlen — Phase-1-Befund). Quellen
sind die geparsten Caches `data/processed/{weather,prices}.parquet`; die Roh-JSONs
unter `data/raw/{weather,prices}/` sind dokumentierter Fallback.

**Lastgang-Fakten:** `value_kw` am Anomalie-Zeitpunkt aus der 15-min-Quelle
(`load_category`), `expected_kw` als Median desselben Wochentags/derselben Uhrzeit
über die 7 Vorwochen, plus `diff_kw`/`diff_pct`. `n_vergleichstage` macht eine dünne
Baseline (nahe Datenstart) sichtbar; bei `expected_kw = 0` bleibt `diff_pct` `None`
statt Division durch null.

**Wetter:** Eine Würzburg-Referenzstation für **alle** Sites — die Standort-PLZ steht
von Rausch noch aus, daher fällt `sites.yaml` einheitlich auf den Würzburg-Default
zurück. Das ist der reale Datenstand, kein stiller Fallback, und wird im Prompt so
ausgewiesen. Temperatur liegt im Parquet bereits in °C vor; Wind wird m/s → km/h
konvertiert, `condition` nach Deutsch gemappt. Fehlt der Stundenwert, sind alle
Wetterfelder `None` ("nicht verfügbar").

**Strompreis:** Day-Ahead ist stündlich; der 15-min-Zeitstempel wird auf seine Stunde
gerundet. EUR/MWh → ct/kWh. Zusätzlich der gleitende 24h-Schnitt als Kontext.

**Mehrkosten (im Code, nie im LLM):** `mehrkosten = diff_kw · dauer_h · preis`. Die
Dauer ist methodenabhängig: bei `cluster_segment` die native Segment-Dauer (nachts 6 h,
vormittag 5 h, mittag 3 h, nachmittag 8 h); bei den Punkt-Methoden
(zscore_stl/arima/autoencoder) aus dem Lastgang im ±2h-Fenster — Anzahl 15-min-Slots
über `expected_kw · 1,2`, mal 0,25 h, begrenzt auf [0,25; 4,0] h. Unterverbrauch
(`diff_kw ≤ 0`) ergibt 0 € (möglicher Effizienzgewinn statt Defekt). Bei negativem
Spotpreis bleibt der echte (ggf. ≤ 0) Wert erhalten und wird im Prompt erläutert.

Stichproben der 5 Test-Anomalien (exakte Werte, die das LLM in Phase 4 sieht):
`reports/llm_evaluation/full_context_samples.md`. Tests:
`tests/test_context.py` (Felder, Wetter-Fallback, Kosten-Edge-Cases).

## LLM-Handlungsempfehlung: Pipeline-Lauf (Phase 4)

Die Produktionspipeline (`scripts/run_llm_pipeline.py`) lief über alle 66 als
`plausibel_anomal` annotierten Anomalien: je Anomalie `build_full_context` →
V2-Production-Prompt (`SYSTEM_PROMPT_PRODUCTION`) → Ollama-Call (`qwen2.5:7b`,
`temperature=0,2`, fester Seed, Schema grammar-erzwungen) → Pydantic-Validierung,
mit bis zu 3 Wiederholungen bei Parse-/HTTP-Fehlern.

**Lauf-Statistik:** 66/66 erfolgreich (100 %), **0 Retries**, **0 Schema-Fehler**.
Wall-Time 8:01 min gesamt, 6,6 s pro Anomalie (warmes Modell). Die strukturelle
Fehlerquote von 0 % bestätigt die zweistufige Garantie (Grammatik + Pydantic) aus
Phase 2 unter Volllast.

**Schweregrad-Verteilung** als Sanity-Check: hoch 32, mittel 25, niedrig 9. Die
Spreizung über alle drei Stufen zeigt **keinen** Modell-Bias zu „alles hoch"; das
Modell stuft auch milde/ambivalente Anomalien entsprechend ein.

**Konfidenz-Kalibrierung pro Methode** (alle im V2-Band 0,75–0,9):

| Methode | n | mean | min–max |
|---|---|---|---|
| zscore_stl | 20 | 0,835 | 0,80–0,85 |
| arima | 17 | 0,818 | 0,75–0,85 |
| cluster_segment | 20 | 0,825 | 0,75–0,85 |
| autoencoder | 9 | 0,844 | 0,80–0,90 |

Zwei methodisch interessante Beobachtungen: Der **Autoencoder** erreicht die höchste
mittlere Konfidenz (0,844) — konsistent mit seiner Pro-Site-Normierung und dem Fokus
auf die Tagesform, der die vorgelegten Anomalien als deutlich erkennbar macht.
**ARIMA** hat die niedrigste (0,818) — seine Forecast-Abweichungen sind nuancierter,
und das LLM stuft sie als weniger eindeutig ein. Die Konfidenz ist hier die des
*Empfehlungsmodells* zur vorgelegten Anomalie, nicht die des Detektors selbst.

**Limitation — HVAC/Beleuchtungs-Default-Hypothese:** Das LLM tendiert dazu, bei
mehrdeutigen Anomalien HVAC-Steuerungsfehler oder Beleuchtungs-Anomalien als primäre
Hypothese vorzuschlagen — eine erfahrungsbasierte Default-Erklärung für
Einzelhandelsgebäude. Diese Empfehlungen sind als **Prüf-Aufträge an das
Facility-Management** zu verstehen, nicht als verifizierte Diagnose. Eine quantitative
Bewertung dieser Hypothesen-Qualität erfordert Vor-Ort-Verifizierung, die im Rahmen
dieser Arbeit nicht möglich war.

**Reproduzierbarkeits-Artefakte:** `reports/llm_recommendations.csv` (66 Zeilen,
12 Spalten) als flache Tabelle; `reports/llm_recommendations/{001..066}.json` mit
vollem Kontext, Prompt und Response je Anomalie für den Dashboard-Detailabruf.

## Flag-Raten und operative Anomalie-Mengen

Bei Standard-Schwellwert (3,0 σ) und X = 0,25 produziert die Pipeline ca. 1–5 %
Flag-Rate je nach Methode (Test-Zeitraum: zscore_stl 3,90 %, autoencoder 1,21 %,
arima 1,05 %, cluster_segment 0,64 %). Bei größeren Standorten ergeben sich daraus
pro Monat operativ relevante Anomalie-Mengen — z. B. rund 240 zscore_stl-Anomalien
für Baumarkt_03 im Januar 2023. Das Dashboard erlaubt über die Hyperparameter-Slider
eine Schwellwert-Anpassung zur Reduktion auf handhabbare Anomalie-Anzahlen je
Reviewer-Aufkommen (Re-Thresholding der vorberechneten Scores, keine Neu-Inferenz).
Eine produktive Pipeline würde Anomalien zusätzlich über Schweregrad und
Ensemble-Überlappung priorisieren.

## Ensemble-Abdeckung auf der validierten Menge

Quantifizierung der Ensemble-Dominanz auf den 66 validierten Anomalien
(`scripts/ensemble_coverage.py` → `reports/tables/ensemble_coverage.csv`).
**Definition:** Methoden-Zugehörigkeit je Anomalie = primäre `method` ∪
`also_flagged_by` aus `annotation.csv`. Die 66 sind per Konstruktion bereits die
prioritäts-deduplizierte **Vereinigung** der Top-20 je Methode — „Ensemble (Union)"
= 66 ist daher trivial; aussagekräftig sind die Pro-Methode-Abdeckung und die
eindeutigen Beiträge.

| Methode | geflaggte validierte Anomalien | davon eindeutig | Precision |
|---|---|---|---|
| zscore_stl | 20 | 17 | 100 % |
| arima | 20 | 17 | 100 % |
| cluster_segment | 20 | 20 | 100 % |
| autoencoder | 9 | 9 | 100 % |
| **Ensemble (Union)** | **66** | — | **100 %** |

Überlappung (von genau k Methoden geflaggt): k=1 → 63, k=2 → 3, k=3/4 → 0.
**Kernaussage:** Das Ensemble liefert 66 validierte Treffer gegenüber der besten
Einzelmethode (20) — **+46 zusätzliche** validierte Anomalien bei durchgehend 100 %
Precision auf der validierten Menge.

**Zwei wichtige Einschränkungen:**
- **Kein Recall.** Es gibt keine vollständige Ground-Truth, nur die validierten
  Top-Kandidaten — die Aussage lautet „mehr validierte Treffer bei gleicher
  Precision", nicht „höherer Recall".
- **Eindeutige Beiträge sind eine Obergrenze.** `also_flagged_by` erfasst nur
  exakte `(site, timestamp)`-Überlappung innerhalb der Top-20; Cross-Granularität
  (cluster = Segment-Tag vs. Punkt-Methoden) bleibt unerfasst, weshalb alle drei
  beobachteten Überlappungen Punkt-Methoden-Paare (zscore↔arima) sind.
