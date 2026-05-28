# Methodology (work in progress)

> Lebendes Methodenkapitel. Wird im Verlauf der Modellierungsphase gefüllt; die finale
> Methodenentscheidung fürs Dashboard wird hier nach dem Methodenvergleich (v4 §5
> Schritt 11+12) dokumentiert.

## Methodenvergleich (drei Methoden)

| Layer | Methode | Status |
|-------|---------|--------|
| Baseline | Z-Score auf STL-Residual | portiert (`models/baseline_zscore.py`) |
| Haupt A | ARIMA pro Cluster | offen |
| Haupt B | Autoencoder (Dense + LSTM) pro Kategorie | offen |

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
- **Schwelle X der Segment-Tag-Aggregation (Schritt 11):** Punkt-Methoden werden für den
  Vergleich auf Segment-Tag hoch-aggregiert. „Irgendein Flag im Segment" (any) bläht die
  Raten auf (ARIMA ~30 %, Z-Score ~14 % auf Segment-Tag). Statt „any" eine **Anteils-/
  Mindestdauer-Schwelle** (X % der Segment-Punkte über Threshold) verwenden — X ist selbst
  ein **Sensitivitätsparameter** und einheitlich für alle Score-Methoden zu variieren.
- **Ensemble statt „welche gewinnt" (offen für Schritt 11):** κ ≈ 0 zwischen Cluster-Distanz
  und den Residual-Methoden (κ ≈ 0,45 zwischen Z-Score und ARIMA) zeigt, dass die Methoden
  **komplementär** sind, nicht redundant. Damit ist „welche Methode gewinnt?" womöglich die
  falsche Frage; ein **Ensemble** (z. B. Vereinigung/Voting der Flags) kann das ehrlichere
  Ergebnis sein. Schritt 11 bleibt für **beide Ausgänge** offen.

## Datenqualität (Stand-/Sonderfälle)

- **Baumarkt_23 – nur 2025-Daten (Leakage-Sonderfall):** Diese Site beginnt erst 2025 und
  hat damit **keinen** Trainingszeitraum (2023–2024). Im Smoke-Lauf greift der ARIMA-Fallback
  „Fit auf voller Site-Reihe" — das ist für diese eine Site faktisch **Train-auf-Testzeitraum**
  (Leakage). **Für die finale Auswertung NICHT stillschweigend mitlaufen lassen:** entweder
  **ganz ausschließen** (zu wenig Historie, empfohlen) oder **transparent als Sonderfall**
  ausweisen. Entscheidung gilt einheitlich für alle Methoden (inkl. Autoencoder-Train/Test).
