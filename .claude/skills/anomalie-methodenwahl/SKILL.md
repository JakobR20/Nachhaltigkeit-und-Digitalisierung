---
name: anomalie-methodenwahl
description: Entscheidungshilfe für die Wahl der passenden Anomalieerkennungs-Methode bei Energiezeitreihen. Aktiv, wenn der Nutzer fragt "welche Methode soll ich nehmen", "Isolation Forest vs LSTM", "Anomalieerkennung implementieren", "Outlier-Detection", "STL", "ARIMA" oder ähnliches. Auch aktiv bei Code-Aufgaben in src/anomaly/.
---

# Anomalieerkennung – Methoden-Entscheidungsbaum

Wir bauen in diesem Projekt **mehrere Methoden parallel** und vergleichen sie. Eine einzelne "beste" Methode gibt es nicht – die Wahl hängt von Datenlage, Erklärbarkeit und Aufwand ab.

## Finale Architektur-Entscheidung (DatenWerKIOS, Stand Mai 2026)

Für die wissenschaftliche Ausarbeitung ist der Stack **festgelegt**. Der generische Entscheidungsbaum unten bleibt als Begründungsgrundlage; die getroffene Wahl ist:

| Rolle | Methode | Begründung (kurz) |
|-------|---------|-------------------|
| **Baseline** | Z-Score auf **Saisonal-Residual** (nicht auf Rohwert) | Einfach, erklärbar, schneller Referenzwert. Residual statt Rohwert, weil die Tages-/Wochensaisonalität sonst dauernd Fehlalarme erzeugt. |
| **Hauptmethode** | **k-Means-Clustering** der Zähler → **(S)ARIMA pro Cluster** → **standardisierte Residuen** als Anomalie-Score | Modelliert zeitliche Struktur explizit; Cluster lösen das Skalierungsproblem von ARIMA bei vielen Zählern; Residuen sind ein interpretierbarer, schwellenfähiger Score. |
| **Handlungsempfehlung** | **Lokales LLM via Ollama** (primär **Qwen2.5 7B-Instruct**, Fallback **Llama 3.1 8B**), Output über **Ollama Structured Outputs** (JSON-Schema) | DSGVO-konform lokal, kein Cloud-Datenabfluss; strukturierter Output für reproduzierbare Empfehlungs-Karten. |
| **Übertragbarkeit** | Training auf Baumärkten, **Test auf ungesehener Branche** (z. B. Tankstellen) | Belegt, dass die Pipeline ohne pro-Standort-Training generalisiert (Forschungsfrage Teil a). |

**Foundation Models** (Chronos, TimeRCD, TranAD, THEMIS): **nur** im State-of-the-Art- und Diskussions-Abschnitt erwähnt, **nicht implementiert**. Begründung fürs Paper: **Erklärbarkeit ist in kritischer Energieinfrastruktur ein essentielles nicht-funktionales Anforderungsmerkmal**, das Foundation-Model-Blackboxes schwer erfüllen – Betreiber müssen einen Alarm nachvollziehen und verantworten können.

### Warum k-Means + ARIMA statt Isolation Forest? (zentrales Verteidigungsargument)

Das ist voraussichtlich die erste Rückfrage in der Verteidigung. Die Argumentationslinie:

1. **Isolation Forest ignoriert die zeitliche Struktur.** Er behandelt jeden Messpunkt (bzw. Feature-Vektor) als unabhängige Beobachtung in einem Merkmalsraum. Die für Energiedaten zentrale **Saisonalität** (Tagesgang, Werktag/Wochenende) muss man ihm erst künstlich als Features (Stunde, Wochentag, Lags) einbauen – und selbst dann lernt er nur eine statische Dichteschätzung, kein zeitliches Modell. Eine Last von 20 kW ist für ihn "normal", weil sie tagsüber oft vorkommt – auch wenn sie um 3 Uhr nachts auftritt.

2. **ARIMA modelliert Saisonalität explizit.** Ein (S)ARIMA-Modell sagt für **jeden Zeitpunkt** den erwarteten Wert *im zeitlichen Kontext* voraus. Das Residuum (Beobachtung − Vorhersage) ist damit per Konstruktion genau die **"Untypischkeit für diesen Zeitpunkt"** – also eine echte Kontext-Anomalie, nicht nur ein absoluter Ausreißer. 20 kW um 3 Uhr nachts erzeugen ein großes Residuum, 20 kW um 14 Uhr nicht.

3. **Erklärbarkeit ist direkt visualisierbar.** ARIMA liefert neben der Punktvorhersage ein **Konfidenzintervall**. Im Dashboard lässt sich „erwarteter Verlauf + Konfidenzband + tatsächlicher Wert" in einem Plot zeigen; eine Anomalie ist sichtbar der Punkt außerhalb des Bandes. Das ist für einen Betreiber sofort nachvollziehbar – ein Isolation-Forest-Score (0–1, ohne physikalische Bedeutung) ist es nicht. Genau das adressiert das nicht-funktionale Requirement Erklärbarkeit.

**Rolle des Clusterings:** ARIMA skaliert schlecht auf viele Einzelzähler (ein Modell pro Zähler ist teuer und überanpassungsanfällig bei kurzen Reihen). k-Means auf normalisierten Tagesprofilen fasst Zähler mit ähnlichem Verbrauchsmuster zusammen; je Cluster wird **ein** ARIMA-Modell trainiert. Das ist sparsamer, robuster und ist zugleich die Grundlage für die **Übertragbarkeit**: Ein neuer Zähler wird einem bestehenden Cluster zugeordnet, statt ein eigenes Modell zu brauchen.

**Ehrliche Limitierung (gehört ins Paper):** Isolation Forest bleibt überlegen, sobald **viele heterogene Features** (Wetter, Preis, Kalender) gleichzeitig einfließen und keine dominante Zeitstruktur vorliegt. Wir führen ihn daher als Vergleichsmethode mit, verwenden aber das ARIMA-Residual als Hauptscore.

## Reihenfolge der Implementierung

**Immer von einfach nach komplex.** Das ist die Reihenfolge aus `CLAUDE.md`:

| Stufe | Methode | Wann sinnvoll? | Wann NICHT? |
|-------|---------|----------------|--------------|
| 0 | Rolling Z-Score / IQR | Immer als Baseline. Schnell, erklärbar. | Bei starker Saisonalität → Residuen erst entfernen. |
| 1 | STL-Decomposition + Residual-Outlier | Klare tägliche/wöchentliche Saisonalität, ein Zähler. | Multivariat oder unregelmäßige Sampling-Frequenz. |
| 2 | Isolation Forest auf Features | Mehrere Features (Wetter, Zeit, Lag), viele Zähler. | Wenn Erklärbarkeit auf Sensor-Ebene wichtig ist. |
| 3 | DBSCAN auf Tagesprofilen | Suche nach untypischen **Tagen**, nicht Stunden. | Bei sehr langen Zeitreihen ohne klare Cluster. |
| 4 | SARIMA + Prediction Interval | Klassisches Forecasting, Anomalie = außerhalb CI. | Bei vielen Zählern (skaliert schlecht). |
| 5 | LSTM-Autoencoder / Prophet | Nur wenn Stufe 0–4 nicht reichen. | Erstwahl. Nie. Erst beweisen, dass die anderen scheitern. |

## Entscheidungs-Heuristiken

Bevor du eine Methode wählst, beantworte:

1. **Univariat oder multivariat?**
   Nur Verbrauch → Stufe 0–1 reichen oft. Verbrauch + Wetter + Preis → Stufe 2+.

2. **Punkt-Anomalie oder Kontext-Anomalie?**
   - **Punkt**: Wert ist absolut zu hoch/niedrig → Z-Score.
   - **Kontext**: Wert ist *für diesen Zeitpunkt* untypisch (20 kW um 3 Uhr nachts) → STL-Residual oder Forecasting.
   - **Kollektiv**: Eine Sequenz ist als Ganzes komisch (3 Tage konstant) → DBSCAN auf Tagesprofilen oder Autoencoder.

3. **Labels vorhanden?**
   - **Nein** (Standard hier) → unsupervised: Isolation Forest, DBSCAN, STL.
   - **Ja, ein paar** → semi-supervised: One-Class SVM auf "normalen" Phasen.
   - **Viele** → supervised (in diesem Projekt eher unwahrscheinlich).

4. **Wie viele Zähler?**
   - **1**: Klassische Zeitreihenmethoden (STL, ARIMA).
   - **10–1000**: ML auf Feature-Matrix (Isolation Forest, DBSCAN).
   - **>1000**: Approximate / Online-Verfahren (HBOS, Streaming-IF) – aber in diesem Projekt vermutlich nicht relevant.

## Implementierungs-Konvention

Jede Methode in diesem Repo bekommt ein eigenes Modul unter `src/anomaly/` mit **sklearn-style API**:

```python
class RollingZScoreDetector:
    def __init__(self, window="7D", threshold=3.0): ...
    def fit(self, series: pd.Series) -> Self: ...
    def predict(self, series: pd.Series) -> pd.Series: ...  # 1 = anomaly, 0 = normal
    def score(self, series: pd.Series) -> pd.Series: ...    # float score
```

Begründung: einheitliche API erlaubt späteren **Methodenvergleich** in einem einzigen Notebook.

## Was bei jeder Methode dokumentiert werden muss

In einem Markdown-Block im jeweiligen Notebook:

- **Annahmen** der Methode (z. B. "geht von Normalverteilung der Residuen aus")
- **Hyperparameter** und wie wir sie gewählt haben (Begründung, nicht Defaults!)
- **Limitierungen** (z. B. "erkennt keine Drift")
- **Geschätzte False-Positive-Rate** (visuell, falls keine Labels)
- **Validierung der Saisonalbereinigung:** Bei jeder residual-basierten Methode (STL, ARIMA) prüfen, ob das **Residuum noch mit externen Treibern korreliert** (v. a. Temperatur). Erwartung: r ≈ 0. Ein deutlich von 0 verschiedenes r heißt, die Saison-/Trendkomponente wurde **unvollständig** abgetrennt → Spezifikation (z. B. STL-`period`, ARIMA-Ordnung) korrigieren. Lehre aus `02_features.ipynb`: stündliche Rohkorrelation täuscht (Tageszyklus überdeckt das Signal) — daher Korrelation auf Tagesaggregaten **und** auf dem Residuum prüfen.

## Was wir NICHT machen

- Direkt mit Deep Learning anfangen – Master-Hausarbeit, nicht Kaggle.
- Methoden mixen, ohne sie einzeln verstanden zu haben.
- Einen "Anomalie-Score" ausgeben, ohne erklären zu können, was er bedeutet.
- Dem Modell ungesehene Daten zum Trainieren geben – Train/Test-Split auch bei unsupervised wichtig (zeitlich, kein Shuffling).
