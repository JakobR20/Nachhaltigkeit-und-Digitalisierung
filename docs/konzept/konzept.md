# Erklärbare, übertragbare Anomalieerkennung im Energieverbrauch von Gewerbeliegenschaften

> **Format:** Wissenschaftliches Paper (~3000 Wörter, max. 12 Seiten) + wissenschaftliches Poster (50/50).
> **Modul:** Nachhaltigkeit und Digitalisierung (Prof. Dr. Michael Müßig, THWS, M. Digital Business Systems).
> **Kooperation:** RAUSCH Technology GmbH · Cluster 2, Aufgabe 3.
> **Bearbeitende:** Jakob & Felix.
>
> Dieses Dokument ist das **Gliederungs-Gerüst** mit inhaltlichen Stichpunkten pro Abschnitt – Grundlage für den ausformulierten Fließtext. Wörterbudget ist je Abschnitt grob annotiert (Summe ≈ 3000).

---

## 0. Kurzfassung / Abstract (~150 Wörter)

- Problem: Steigender Energiekostendruck und ESG-Pflichten erfordern frühzeitiges Erkennen von Verbrauchsanomalien in Gewerbeliegenschaften.
- Lücke: Verbreitete ML-Detektoren sind entweder schwer erklärbar (Foundation Models) oder ignorieren die Zeitstruktur (Isolation Forest); zudem erfordern viele Ansätze pro-Standort-Training.
- Beitrag: Eine erklärbare Pipeline (Clustering → ARIMA-Residuen → lokales LLM für Handlungsempfehlungen), die ohne pro-Standort-Training auf neue Branchen übertragbar ist.
- Ergebnis (in Stichworten): Saisonalität dominant täglich/wöchentlich; ARIMA-Residuen liefern interpretierbare Kontext-Anomalien; Übertragbarkeitstest auf ungesehener Branche.

## 1. Einleitung (~350 Wörter)

- **Motivation:** Energieeffizienz als ökologisch *und* ökonomisch relevanter Hebel; Smart-Meter-Rollout liefert die Datengrundlage, aber Rohdaten allein erzeugen keinen Mehrwert.
- **Problemstellung:** Anomalien (Defekte, Fehlsteuerungen, ineffiziente Nachtlasten) bleiben in 15-min-Lastgängen unentdeckt; manuelle Sichtung skaliert nicht über viele Liegenschaften.
- **Forschungsfrage (explizit):** *„Wie lässt sich eine erklärbare Anomalieerkennungs-Pipeline für Energieverbrauchsdaten entwickeln, die (a) ohne pro-Standort-Training auf neue Liegenschaften übertragbar ist und (b) automatisierte Handlungsempfehlungen generiert?"*
- **Beitrag (explizit):** (1) eine erklärungszentrierte Methodenauswahl mit Begründung gegen Black-Box-Verfahren; (2) ein cluster-basierter Forecasting-Ansatz, der Übertragbarkeit ohne pro-Standort-Training ermöglicht; (3) Integration eines lokalen LLM zur DSGVO-konformen Generierung strukturierter Handlungsempfehlungen; (4) ein lauffähiger Prototyp auf realen RAUSCH-Daten als Machbarkeitsbeleg.
- **Abgrenzung:** Pflichtabgabe ist Paper + Poster; der Prototyp ist Beleg, nicht Produktreife.

## 2. Stand der Forschung (~450 Wörter)

- **Klassische statistische Verfahren:** Z-Score/IQR auf Residuen, STL-Dekomposition, (S)ARIMA mit Prädiktionsintervall – stark in Erklärbarkeit, etabliert in der Energiezeitreihen-Literatur.
- **Klassisches ML (unsupervised):** Isolation Forest, DBSCAN, One-Class-SVM, k-Means auf Tagesprofilen – gut bei multivariaten Features, aber zeit-agnostisch bzw. nur dichtebasiert.
- **Deep Learning / Foundation Models:** Chronos (Zeitreihen-Foundation-Model), TimeRCD, TranAD (Transformer-Autoencoder für Anomalien), THEMIS – hohe Leistung, aber Black-Box-Charakter.
- **Forschungslücke / Positionierung:** Wir argumentieren, dass in **kritischer Energieinfrastruktur Erklärbarkeit ein nicht-funktionales Pflichtmerkmal** ist (Nachvollziehbarkeit, Haftung, Akzeptanz beim Betreiber). Foundation Models werden daher **diskutiert, aber bewusst nicht implementiert**.
- **Übertragbarkeit als offener Punkt:** Die meisten Ansätze trainieren je Standort; Generalisierung über Branchen hinweg ist unterbeleuchtet → Anknüpfungspunkt unseres Beitrags.

## 3. Datenbasis (~350 Wörter)

- **Primärdaten (RAUSCH):** 77 Excel-Lastgänge in fünf Branchen (Baumärkte, Ladestationen, Tankstellen, Handel, Büro); 15-min-Auflösung; Leistung in kW bzw. Energie in kWh; Zeitraum bis 2023–2026. Details und Inventar in `docs/konzept/datenprofil.md`.
- **Hauptdatensatz:** **Baumärkte** (26 Zähler, kW). **Validierung:** Handel/Lastgang_34 (kWh, mit Status-Flag).
- **Datenqualität (aus EDA, `notebooks/01_eda.ipynb`):** keine Duplikate, keine Negativwerte, überschaubare Zeit-Lücken; **3 flache Zähler** (`vmax < 1 kW`: Baumarkt_01/_02/_04) – wahrscheinlich Einheiten-Bug (W statt kW) oder Unterzähler, mit Marja zu klären, vorerst ausgeschlossen.
- **Saisonalität (Befund):** dominant **täglich + wöchentlich** (ACF-Peaks bei lag 24/168), Jahreskomponente sekundär; drei typische Tagesprofil-Cluster (k=3 via Silhouette).
- **Externe Datenquellen (mit Begründung):** **DWD-Wetter** (Temperatur → Heiz-/Kühllast, Jahreskomponente), **EPEX-Strompreis** (Kontext für preisinduzierte Laständerungen), **Kalender** (Feiertage/Ferien → erklärt Sonderschließtage). Bezug per Caching, siehe Skill `external-data-apis`.

## 4. Methodischer Rahmen & Anforderungen (~250 Wörter)

- **Anomalie-Typologie:** Punkt- vs. Kontext- vs. Kollektiv-Anomalie; Fokus liegt auf **Kontext-Anomalien** (untypisch *für diesen Zeitpunkt*).
- **Nicht-funktionale Anforderungen:** Erklärbarkeit (Betreiber muss Alarm verstehen), DSGVO-Konformität (Smart-Meter sind personenbeziehbar → lokale Verarbeitung), Übertragbarkeit, Reproduzierbarkeit.
- **Vorgehensprinzip:** einfach → komplex; mehrere Methoden parallel und vergleichen statt eine „fancy" Methode (vgl. Skill `anomalie-methodenwahl`).
- **Evaluationsstrategie ohne Labels:** „ground-truth-lite" aus visuell offensichtlichen Anomalien; zeitlicher Train/Test-Split (kein Shuffling).

## 5. Architektur des Prototyps (~900 Wörter, Kern)

- **Pipeline-Überblick (Datenfluss):** Smart-Meter (Excel) → `loader` (Normalisierung, tz, stabile meter_ids) → Feature-Engineering (+ Wetter/Preis/Kalender) → Detection-Stufen → Anomalie-Score → LLM-Empfehlung → Dashboard. Abbildung: `01_datenflussdiagramm.png`.

### 5.1 Baseline: Z-Score auf Saisonal-Residual (~120 Wörter)

- Saisonkomponente (Tag/Woche) via STL entfernen, globaler Z-Score je Zähler auf dem Residuum (`stl_resid`); Anomalie bei |z| > 3. Umgesetzt in `notebooks/03_baseline_zscore.ipynb` / `src/anomaly/zscore.py`.
- Begründung: schnelle, voll erklärbare Referenz; Residual statt Rohwert, sonst Dauer-Fehlalarme durch Tagesgang.
- Annahmen/Limit: näherungsweise normalverteilte Residuen; erkennt keine Drift.
- **Die Baseline diente primär als Vergleichsmaßstab; die empirische Evaluation hat systematische Limitationen aufgedeckt, die die Wahl der Hauptmethode motivieren — siehe Abschnitt 6 (Ergebnisse) und 8 (Diskussion).**

### 5.2 Hauptmethode: Clustering + ARIMA + standardisierte Residuen (~400 Wörter)

- **Schritt 1 – Clustering:** k-Means auf normalisierten mittleren Tagesprofilen fasst Zähler mit ähnlichem Muster zusammen (k=3 aus EDA). Zweck: ARIMA skaliert schlecht pro Einzelzähler; ein Modell je Cluster ist sparsamer und robuster.
- **Schritt 2 – Forecasting:** (S)ARIMA je Cluster modelliert den erwarteten Verlauf inkl. Saisonalität; Hyperparameter begründet wählen (ACF/PACF, AIC), nicht Defaults.
- **Schritt 3 – Score:** standardisierte Residuen (Beobachtung − Vorhersage, skaliert) als kontinuierlicher Anomalie-Score; Schwelle über Prädiktionsintervall.
- **Validierung der Saisonalbereinigung (empirisch belegt, `02_features.ipynb`):** Die STL-Spezifikation (period=168) ist *validiert*, weil das **Residuum nicht mehr signifikant mit dem Wetter korreliert** (Temperatur↔STL-Residuum median r ≈ 0,02). Das heißt: STL hat Trend, Wetter- und Saisonanteil **sauber absorbiert** — das Residuum ist die „echte" Untypischkeit und nicht bloß eine ungemodellte Saison-/Wetterschwankung. Ein deutlich von 0 verschiedenes r wäre umgekehrt ein Hinweis auf eine **fehlerhafte Zerlegung**.
- **Begründung „k-Means + ARIMA statt Isolation Forest" (ausführlich – erwartete Verteidigungsfrage):**
  1. **Isolation Forest ignoriert die zeitliche Struktur.** Er bewertet Punkte als unabhängige Beobachtungen im Merkmalsraum; Saisonalität muss künstlich als Features eingebaut werden und bleibt eine statische Dichteschätzung. 20 kW gelten als „normal", weil tagsüber häufig – auch nachts um 3 Uhr.
  2. **ARIMA modelliert Saisonalität explizit.** Die Vorhersage *für jeden Zeitpunkt* macht das Residuum per Konstruktion zur **„Untypischkeit für diesen Zeitpunkt"** – eine echte Kontext-Anomalie. 20 kW nachts → großes Residuum; 20 kW mittags → kleines.
  3. **Erklärbarkeit ist direkt visualisierbar.** ARIMA liefert ein **Konfidenzintervall**; „erwarteter Verlauf + Konfidenzband + Ist-Wert" ist in einem Dashboard-Plot sofort nachvollziehbar – ein IF-Score (0–1, ohne physikalische Bedeutung) nicht. Genau das erfüllt das Erklärbarkeits-Requirement.
- **Beitrag zur Übertragbarkeit (strukturierte Adaption, nicht „plug-and-play"):** Eine neue Liegenschaft/Branche wird nicht blind übernommen, sondern über ihr mittleres Tagesprofil mit den vorhandenen **Cluster-Centroiden** verglichen. Ist die Distanz unter einer definierten Schwelle → das **bestehende ARIMA-Modell des nächsten Clusters** wird genutzt (kein Training). Liegt sie darüber → **Warnung „neues Cluster nötig"** bzw. ein **Default-ARIMA** als Fallback. So entsteht Übertragbarkeit mit *minimalem* Adaptionsaufwand statt der überzogenen Behauptung, die Pipeline laufe auf jeder Branche ungetestet.
- **Ehrliche Limitierung:** Bei vielen heterogenen Features ohne dominante Zeitstruktur ist IF überlegen → wird als Vergleichsmethode mitgeführt, nicht als Hauptscore.

### 5.3 Handlungsempfehlung: lokales LLM via Ollama (~250 Wörter)

- **Aufgabe:** aus erkannter Anomalie + Kontext (Zeit, Tagesprofil-Abweichung, Wetter/Preis) eine **strukturierte Empfehlungs-Karte** generieren (Schweregrad, Vermutung, vorgeschlagene Maßnahme).
- **Warum lokal (Ollama):** Smart-Meter-Daten sind DSGVO-relevant → kein Cloud-Abfluss; reproduzierbar, kostenfrei, offline.
- **Format-Garantie:** **Ollama Structured Outputs** (JSON-Schema, constrained decoding auf Token-Ebene) erzwingt das Ausgabeformat – Format-Treue hängt damit primär an dieser Funktion, nicht am Modell.
- **Modellwahl (Recherche, M-Series Mac):** primär **Qwen2.5 7B-Instruct**, Fallback **Llama 3.1 8B**. Begründung in der Tabelle:

| Modell | Q4-Größe / RAM | Speed (M3 Pro) | Deutsch | Strukturierter Output |
|--------|----------------|----------------|---------|------------------------|
| **Qwen2.5 7B-Instruct** ⭐ | ~4,5 GB / 16 GB | ~18–25 tok/s | sehr gut (stark multilingual) | sehr gut; Benchmarks > Llama 3.1 8B & Gemma 2 9B (außer IFEval) |
| **Llama 3.1 8B** (Fallback) | ~5 GB / 16 GB | ~18–25 tok/s | gut | stark im Instruction-Following (IFEval), größte Tooling-Basis |
| Gemma 2 9B | ~5,5 GB / ≥18 GB | etwas langsamer | sehr gut (europäisch stark) | gut |
| Mistral 7B | ~4,1 GB / 16 GB | schnell | schwächer/älter | mittel — deprioritisiert |

  Kernpunkt: Da Ollamas Structured Outputs das Format ohnehin erzwingen, entscheidet primär die Größe/Deutsch-Balance → Qwen2.5 7B.

### 5.4 Übertragbarkeits-Test (~130 Wörter)

- **Leitfrage (offen formuliert):** *„Wie weit trägt die Cluster-Zuordnung über Branchen hinweg?"* — also nicht „funktioniert auf neuer Branche", sondern eine empirisch zu beantwortende Frage.
- **Aufbau:** Pipeline auf **Baumärkten** trainieren (Clustering + ARIMA-Modelle je Cluster), dann auf einer **ungesehenen Branche** (z. B. Tankstellen) die mittleren Tagesprofile gegen die Baumarkt-Centroide matchen.
- **Messgrößen:** Anteil der Fremd-Zähler, die unter der Distanzschwelle einem Cluster zuordenbar sind; Verteilung der Residuen-Scores im Vergleich zu den Trainingszählern; visuell geprüfte Fehlalarmrate.
- **Mögliche Ergebnisse offen halten:** Von „Zuordnung trägt gut" bis „Fremdbranche braucht eigenes Cluster" — beide Ausgänge sind ein verwertbares Resultat und adressieren Teil (a) der Forschungsfrage.

## 6. Evaluation (geplant) (~250 Wörter)

- **Methodenvergleich:** Baseline (5.1) vs. Hauptmethode (5.2) vs. Isolation Forest (Referenz) auf denselben Zählern.
- **Metriken ohne Labels:** Übereinstimmung mit „ground-truth-lite", Stabilität über Zähler, geschätzte False-Positive-Rate (visuell), Rechenaufwand.
- **Erklärbarkeits-Bewertung:** qualitativ – kann ein Betreiber den Alarm anhand des Dashboards nachvollziehen?
- **Übertragbarkeit:** Vergleich der Score-Verteilungen Baumärkte (train) vs. Fremdbranche (test).
- Tabellen-/Abbildungsverweise: Methodenvergleich, Beispiel-Anomalie mit Konfidenzband.
- **Befund: Wetter-Korrelation ist auflösungsabhängig (methodisches Sorgfalts-Argument).** Eine naive Korrelation würde in die Irre führen; erst die mehrstufige Analyse zeigt das wahre Signal:

  | Auflösung | Temp↔Verbrauch | Lesart |
  |-----------|----------------|--------|
  | stündlich, roh | r ≈ 0,11 | scheinbar irrelevant — Tageszyklus überdeckt das Signal (Artefakt) |
  | Tagesmittel | median r ≈ −0,32 (22/23 Zähler negativ) | klares **Heizsignal**: kältere Tage → mehr Verbrauch |
  | STL-Residuum | median r ≈ 0,02 | STL hat das Wetter bereits in Trend + Saison absorbiert |

  Quelle: `02_features.ipynb`. Kernaussage: Wetter ist auf Saisonebene ein realer Treiber, im Residuum aber bereits herausgerechnet.

- **Faktenbox: Ergebnisse der Z-Score-Baseline** (`03_baseline_zscore.ipynb`):
  - **14.712 Anomalien** bei |z| > 3; Rate **1,7–3,2 %** pro Zähler (über alle Zähler bemerkenswert gleichmäßig).
  - Beobachtete **2,84 %** statt theoretischer **0,27 %** → **fat-tailed Residuen** (Schwelle empirisch kalibrieren, nicht aus der Normalverteilung).
  - **Top-10-Anomalien sind durchweg Feiertage** (negative Residuen / Schließtage) → operative False Positives.
  - **Wochenenden werden problemlos absorbiert** (STL erkennt die Wochenstruktur) — die Fehlalarme entstehen an den *irregulären* Feiertagen.

## 7. Dashboard-Konzept / Wireframe (~250 Wörter)

- **Übersichtskarte:** KPIs (Anomalien letzte 7 Tage, betroffene Zähler, geschätzter Mehrverbrauch in kWh).
- **Zeitreihen-Panel:** Lastgang mit ARIMA-Erwartung + Konfidenzband + hervorgehobenen Anomalie-Bereichen (das Erklärbarkeits-Kernbild).
- **Anomalie-Liste:** Timestamp, Zähler, Schweregrad, LLM-Handlungsempfehlung.
- **Drilldown:** Kontext einer Anomalie (Wetter, Preis, Tagesprofil-Abweichung).
- **Filter:** Zeitraum, Zähler, Anomalie-Typ.
- Statischer Mockup (Pflicht, Excalidraw → PNG); optional Streamlit-Prototyp (`src/viz/dashboard.py`). Verweis auf Poster.

## 8. Diskussion (~200 Wörter)

- **Erklärbarkeit vs. Leistung:** bewusster Verzicht auf Foundation Models; Trade-off offen benennen (evtl. geringere Detektionsrate gegen volle Nachvollziehbarkeit).
- **Grenzen der Methode:** ARIMA-Annahmen (Stationarität nach Differenzierung), Cluster-Stabilität bei Branchenwechsel, Kaltstart bei neuen Mustern.
- **LLM-Risiken:** Halluzination in Empfehlungen → durch strukturierten Output und regelbasierte Leitplanken eingegrenzt; LLM erklärt, entscheidet aber nicht autonom.
- **Wetter-Robustheit der Methodenwahl:** Da das STL-Residuum empirisch wetterunabhängig ist (r ≈ 0,02), kommt die Z-Score-Baseline ohne explizite Wetterkorrektur aus — ein Robustheits- und Einfachheitsvorteil. Wetterfeatures bleiben für Erklärung/Plausibilisierung, nicht als Pflichteingang des Anomalie-Scores.
- **Datenqualität:** flache Zähler, Lücken, fehlende Labels.

### Limitationen der Z-Score-Baseline → Übergang zur Hauptmethode

Die empirische Auswertung der Baseline (`03_baseline_zscore.ipynb`) legt vier systematische Schwächen offen — jede motiviert eine konkrete Eigenschaft der ARIMA-Hauptmethode:

- **L1 – Fat-tailed Residuen:** beobachtete Rate 2,84 % statt 0,27 % (~10×). → *Konsequenz:* Schwelle **empirisch kalibrieren**, nicht aus der 3-Sigma-Annahme ableiten.
- **L2 – Keine Feiertags-Awareness (Hauptbefund):** STL lernt die regelmäßige Wochenstruktur, aber keine irregulären Feiertage → alle Top-10-„Anomalien" sind Schließtage. → *Konsequenz:* **SARIMAX mit exogenem `is_holiday`** (Features liegen in `features.parquet` bereit); zusätzlich kann die LLM-Schicht „Feiertag" als Kontext entschärfen.
- **L3 – Heteroskedastizität:** ein globaler σ je Zähler über-flaggt Geschäftsstunden und unter-flaggt ruhige Phasen. → *Konsequenz:* **kontextabhängiges Prädiktionsintervall** (ARIMA) statt globalem Z-Score.
- **L4 – Kein zeitlicher Kontext:** Punkt-Scoring ohne Bewertung von Dauer/Sequenz. → *Konsequenz:* Forecasting-basierte Methode bewertet Abweichungen über die Zeit hinweg.

## 9. Nachhaltigkeit & Geschäftsmodell (~250 Wörter)

- **Nachhaltigkeits-Verknüpfung (Müßig):** Digitalisierung als Mittel zur Effizienz; Einordnung in die 8 Dimensionen der Nachhaltigkeit (Vogt), Schwerpunkt ökologisch + ökonomisch + digital.
- **SDG-Bezug:** SDG 7 (bezahlbare, saubere Energie), SDG 9 (Innovation/Infrastruktur), ggf. SDG 12 (verantwortungsvoller Verbrauch).
- **Stakeholder/Geschäftsmodell:** Betreiber (Kostensenkung), Stadtwerk/RAUSCH (Mehrwertdienst auf bestehender Zähler-Infrastruktur), KMU ohne eigenes Energieteam.
- **DatenWerKIOS-Anknüpfung:** Einbettung in die offene Datenplattform; lokale, DSGVO-konforme Verarbeitung als Vertrauensargument.
- **Modellwahl LLM:** siehe Abschnitt 5.3.

## 10. Fazit & Ausblick (~200 Wörter)

- Antwort auf die Forschungsfrage (a + b) in zwei, drei Sätzen.
- Was fehlt für Produktivbetrieb: echte Labels, Online-/Streaming-Betrieb, automatisiertes Retraining, Integration weiterer Branchen.
- Welche Daten würden den Mehrwert erhöhen (Sub-Metering, Anlagenstammdaten).

## 11. Literatur (APA)

- Durchgehend APA; Online-Quellen mit Abrufdatum; jede Abbildung mit Quelle (auch „Eigene Darstellung").
- Zu zitieren u. a.: Isolation Forest (Liu et al.), STL (Cleveland et al.), ARIMA (Box & Jenkins), Chronos/TranAD/THEMIS, DSGVO-Bezug Smart Metering, SDG/Vogt.

---

### Abbildungs-Backlog (nach `paper-poster-thws`-Konvention, `docs/konzept/abbildungen/`)
- `01_datenflussdiagramm.png` – Pipeline-Überblick (noch zu erstellen)
- Vorhandene EDA-Abbildungen (umbenennen/auswählen für Druck): Tagesprofil, Calendar-Heatmap, Cluster-Profile, ARIMA-Beispiel mit Konfidenzband (noch zu erstellen).
