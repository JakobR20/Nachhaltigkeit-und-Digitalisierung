# CLAUDE.md – Patch v4
## Architektur-Update nach Rausch-Feedback (26.05.2026)

> Dieser Patch ergänzt / korrigiert den CLAUDE.md-Brief v3. Vier konkrete Änderungen an Methoden-Stack und Setup. In Claude Code als neue Session starten und vor der Implementierung lesen.

---

## 1. Was sich ändert

### 1.1 Drei Methoden im empirischen Vergleich

Rausch hat den Autoencoder als „sehr gut geeignet" benannt. Statt diese Methodenwahl rein durch Industriepartner-Autorität zu rechtfertigen, **vergleichen wir empirisch drei Methoden** und lassen die Daten entscheiden. Der Methodenvergleich wird zum eigenen Ergebnis-Kapitel im Paper.

| Layer | Methode | Rolle |
|-------|---------|-------|
| Baseline | Z-Score auf STL-Residual | Naive Referenz, voll erklärbar |
| **Haupt A** | **ARIMA pro Cluster** | **Klassische Forecasting-Methode** |
| **Haupt B** | **Autoencoder (Dense + LSTM) pro Kategorie** | **Deep-Learning-Ansatz** |
| Diagnose | Multi-Resolution Clustering | Voraussetzung für ARIMA + Diagnose-Schicht für AE |
| Empfehlung | Lokales LLM (Llama 3.2 3B via Ollama) | Strukturierte Empfehlungs-Karte |

**Vergleichsmetriken (im Paper als Ergebnis-Tabelle):**
- Geschätzte Precision aus manueller Annotation der Top-Anomalien (Stichprobe ≈ 200 Punkte)
- Übereinstimmung der Methoden (Cohen's Kappa) – finden alle Methoden dieselben Anomalien?
- Inferenzzeit pro Standort (Dashboard-Realität)
- Erklärbarkeit qualitativ (Konfidenzband ARIMA vs. Rekonstruktionsfehler-Kurve AE)

**Welche Methode kommt ins finale Dashboard?** Entscheidung am Ende der Modellierungsphase auf Basis der Vergleichstabelle – nicht vorab gesetzt. Dokumentation der Entscheidung in `methodology.md`.

**Für das Paper:** Methodenwahl ist nicht beliebig, sondern wurde nach Industriepartner-Konsultation iteriert und empirisch validiert. Beide Ausgänge sind verwertbar: Wenn AE gewinnt → Industrie-Empfehlung empirisch bestätigt. Wenn ARIMA gewinnt → ehrliches Resultat („einfacheres Modell schlug komplexeres bei kontextueller Anomalieerkennung").

### 1.2 Multi-Resolution-Clustering (Tageszeit-Segmente)

Bisher: k-Means auf 96-dim Tagesprofilen → ein Cluster-Label pro Tag.

Neu, zusätzlich: **Clustering pro Tageszeit-Segment.** Default-Schnitte (in `config.yaml` änderbar):

| Segment | Zeitfenster | Begründung |
|---------|-------------|------------|
| Nachts       | 00:00 – 06:00 | Stand-by, Basislast |
| Vormittag    | 06:00 – 11:00 | Hochlauf, Morgenpeak |
| Mittag       | 11:00 – 14:00 | Mittagsspitze (Gewerbe) |
| Nachmittag   | 14:00 – 22:00 | Hauptgeschäftszeit / Abendlast |

Pro Standort × Tag entstehen damit fünf Cluster-Zuordnungen (Tagesprofil + 4 Segmente). Anomalien werden über die Segment-Zuordnung **diagnostiziert**: „Welche Tageszeit ist auffällig?" Das ist der direkte Input für die Handlungsempfehlung.

**Doppelte Rolle des Clusterings:**
- **Für ARIMA:** Voraussetzung – ARIMA pro Einzelzähler skaliert nicht; ARIMA-Modelle werden pro Cluster trainiert.
- **Für Autoencoder:** nachgeschaltete Diagnose-Schicht – Segment-Cluster-Labels erklären, *welche* Tageszeit ein Rekonstruktionsfehler betrifft, ohne in das AE-Training einzugehen.

### 1.3 Cross-Category-Transfer wird aufgegeben

Rauschs Einschätzung: Modell auf Baumärkten trainieren → auf Tankstellen anwenden funktioniert wahrscheinlich nicht. Das ist plausibel, weil die Lastprofile zwischen Kategorien drastisch unterschiedlich sind (siehe Drei-Kategorien-Plot auf Folie 4 des Pitches).

**Konsequenz für die Architektur:**
- Pro Kategorie eigene Autoencoder-, ARIMA- und Cluster-Modelle trainieren.
- Keine kategorieübergreifenden Cross-Tests im Paper.
- Übertragbarkeit-Frage bleibt – aber nur **innerhalb derselben Kategorie**: trainieren auf z. B. 4 Baumärkten, anwenden auf einen 5. Baumarkt. Das ist die methodisch tragfähige Variante.
- Folie 6 der internen Architektur-PPT (`Übertragbarkeit: Cluster-Zuordnung über Branchen hinweg`) wird im Paper anders formuliert: **Innerhalb-Kategorie-Generalisierung** statt Cross-Category-Transfer.

### 1.4 Standortgenaues Wetter (PLZ geliefert — Würzburg-Default entfallen)

**✓ Aufgelöst (Stand 2026-06-22).** Die Baumarkt-Exporte tragen die PLZ im Dateinamen.
Die Zuordnung frozen-ID (03, 05–26) → PLZ wurde per Inhalts-Fingerprint (Stundenmittel vs.
`features.parquet`, Match 1.000) verifiziert — nicht über die automatische meter_id. Daraus:

- Echte Koordinaten je Standort (PLZ-Centroid via `pgeocode`) in `config/sites.yaml`.
- Wetter wird je Standort gezogen (`data/processed/weather_by_site.parquet`, MultiIndex
  site/timestamp) und in der LLM-Schicht site-genau gematcht (`_lookup_weather(site, ts)`).
- Würzburg-Default (49.7913 / 9.9534, BY) und der `defaults:`-Block in `sites.yaml` sind entfernt.
- Verbleibende Limitation: Das `feiertag`-Flag der eingefrorenen `annotation.csv` nutzt noch den
  BY-Kalender; eine Neuberechnung würde das frozen-Artefakt verändern und unterbleibt bewusst.

Zuordnungstabelle und Befunde (u. a. Baumarkt_16≡18, 20≡21 inhaltsgleich): `reports/site_plz_mapping.md`.
Der ursprüngliche Default-Mechanismus (unten) bleibt als historische Referenz dokumentiert.

---

## 2. Patch für `config/sites.yaml`

```yaml
defaults:
  lat: 49.7913
  lon: 9.9534
  bundesland: BY
  lat_lon_source: default_wuerzburg
  fallback_reason: "Postleitzahlen werden von Rausch noch geliefert (Status 26.05.2026)"

sites:
  - id: baumarkt_01
    file: data/raw/rlm/baumarkt_01.xlsx
    category: baumarkt
    # lat/lon/bundesland fallen aktuell auf defaults zurück
    operating_hours: "Mo-Sa 07:00-20:00"
    connected_load_kw: null
    plz: null              # wird nach Rausch-Lieferung ergänzt
  # ... weitere Sites analog
```

**Loader-Verhalten (`rlm_loader.py`):** Wenn `lat`/`lon`/`bundesland` auf Site-Ebene null sind, werden die Defaults aus `defaults:` übernommen und im Log eine WARNING geschrieben: `Using default Würzburg coords for site=<id> (plz pending from Rausch)`. So sieht man beim Pipeline-Lauf sofort, welche Standorte noch nicht final konfiguriert sind.

---

## 3. Patch für `config/config.yaml`

```yaml
clustering:
  tagesprofile:
    enabled: true
    k_values: [2, 3, 4, 5]      # Elbow-/Silhouette-Suche
    dim: 96                      # 24h × 4 Werte
  segmente:
    enabled: true
    segments:
      - name: nachts
        start_hour: 0
        end_hour: 6
      - name: vormittag
        start_hour: 6
        end_hour: 11
      - name: mittag
        start_hour: 11
        end_hour: 14
      - name: nachmittag
        start_hour: 14
        end_hour: 22
    features_per_segment: [mean, max, std, slope]
    k_values: [2, 3, 4]

models:
  zscore:
    enabled: true
    threshold: 3.0
    stl_period: 96   # 24h auf 15-min-Basis
  arima:
    enabled: true
    selection: auto    # ACF/PACF + AIC-basiert
    seasonal: true
    one_model_per_cluster: true
  autoencoder:
    enabled: true
    variants: [dense, lstm]
    window_hours: 24
    one_model_per_category: true
    seed: 42

evaluation:
  precision_sample_size: 200
  kappa_pairwise: true
  inference_timing: true
```

Damit sind alle drei Methoden parallel über Flags steuerbar und ihre Hyperparameter sichtbar.

---

## 4. Patch für die Projektstruktur

```
src/schadschoepfung/
├── features/
│   ├── daily_profile.py        # bleibt – 96-dim Tagesprofil
│   ├── segments.py             # NEU – pro Tag × Segment Aggregat-Features
│   └── ...
├── models/
│   ├── clustering_daily.py     # bleibt
│   ├── clustering_segments.py  # NEU – k-Means pro Segment
│   ├── baseline_zscore.py      # bleibt – einfachste Methode
│   ├── arima_clustered.py      # NEU bzw. umbenannt – ARIMA pro Cluster (Hauptmethode A)
│   ├── autoencoder_dense.py    # bleibt – Hauptmethode B
│   └── autoencoder_lstm.py     # bleibt – Hauptmethode B (Variante)
├── evaluation/
│   ├── threshold.py
│   ├── metrics.py
│   ├── method_comparison.py    # NEU – Precision, Kappa, Inferenzzeit
│   └── ...
├── diagnosis/
│   └── anomaly_classifier.py   # NEU – verbindet Anomalie-Score mit Segment-Cluster-Label
```

`evaluation/method_comparison.py` ist der zentrale Vergleichs-Driver: füttert dieselbe annotierte Stichprobe in alle drei Methoden, baut die Vergleichstabelle, exportiert Plots für das Paper.

`diagnosis/anomaly_classifier.py` ist die Brücke vom Anomalie-Score (egal welcher Methode) zur Diagnose. Eingabe: ein Zeitstempel mit hohem Score. Ausgabe: Anomalie-Karte mit Segment-Zuordnung („Nachmittag, Cluster 3 = ungewöhnlich hoch") + Kontext für das LLM-Prompting. Methoden-agnostisch implementiert, damit ein späterer Wechsel zwischen ARIMA und AE im Dashboard ohne Refactoring funktioniert.

---

## 5. Schrittfolge für Claude Code

In der Reihenfolge, weil aufeinander aufbauend:

1. **`config/sites.yaml`** mit Würzburg-Defaults anlegen (Abschnitt 2).
2. **`config/config.yaml`** um Clustering- und Models-Blöcke erweitern (Abschnitt 3).
3. **`rlm_loader.py`** Defaults-Fallback einbauen mit klarem WARNING-Logging.
4. **`features/segments.py`** + Pflichttests.
5. **EDA-Notebook 03 erweitern**: Segment-Features visualisieren, Silhouette-Score plotten.
6. **`clustering_daily.py` + `clustering_segments.py`** – beide Cluster-Varianten trainieren, Modelle persistieren.
7. **`baseline_zscore.py`** – einfachste Methode zuerst, ist quasi geschenkt.
8. **`arima_clustered.py`** – ARIMA pro Cluster mit auto.arima-Logik (ACF/PACF + AIC). Hier liegt der größte Aufwand der drei Methoden.
9. **`autoencoder_dense.py`** – pro Kategorie.
10. **`autoencoder_lstm.py`** – pro Kategorie.
11. **`evaluation/method_comparison.py`** – Vergleichstabelle, Cohen's Kappa, Inferenzzeit.
12. **Manuelle Annotation** ~200 Anomalie-Kandidaten als CSV im Repo – wird Eingang für Precision-Schätzung.

**Erst nach 11+12** Entscheidung für die Dashboard-Hauptmethode treffen und in `methodology.md` dokumentieren.

---

## 6. Zeit-Realismus (ehrlich)

Drei Methoden + Clustering + LLM + Dashboard bis 02.07. ist sechs Wochen – knapp, aber machbar, wenn:

- Schritt 1–6 **bis 03.06.** stehen (1 Woche).
- Schritte 7+8 **bis 10.06.** (ARIMA-Tuning ist der größte Posten).
- Schritte 9+10 **bis 17.06.** (Autoencoder-Training parallelisierbar).
- Schritt 11+12 **bis 24.06.** (Vergleichs-Auswertung + Annotation).
- Bis 02.07. dann LLM-Empfehlung, Dashboard, Paper-Finalisierung.

**Risiko-Mitigation:** Wenn ARIMA-Implementierung bis 10.06. nicht funktioniert (z. B. Cluster-spezifische Saisonalität sperrig), gilt die einfache Variante: nur `(p,d,q)`-Modell ohne Saisonalität, schnell trainiert, ehrlich im Paper als „grobe Forecasting-Baseline" beschrieben. Das ist methodisch besser als „wir haben ARIMA versprochen und nicht geliefert".

---

## 7. Konsequenzen für das Paper

- **Methodenvergleich als Ergebnis:** zentrales Element des Ergebnis-Kapitels, nicht im Anhang versteckt. Tabelle mit Precision / Kappa / Inferenzzeit, plus eine narrative Diskussion „Welche Methode würden wir wann empfehlen?".
- **Methoden-Iteration sauber dokumentieren:** Industriepartner empfahl Autoencoder, wir haben den empirischen Vergleich aufgesetzt, um die Empfehlung zu validieren. Stärkt den wissenschaftlichen Anspruch.
- **Tageszeit-Segmentierung als Verbindung Methodenteil ↔ Empfehlungsteil:** liefert direkt verwertbaren Kontext für die LLM-Empfehlung.
- **Übertragbarkeit neu formuliert:** „Innerhalb-Kategorie-Generalisierung" statt Cross-Category-Transfer.
- **Würzburg-Default als Limitation:** explizit als Sensitivitäts-Diskussion in `methodology.md`.

---

*Patch-Version v4 – Z-Score + ARIMA + Autoencoder als drei gleichberechtigte Methoden im empirischen Vergleich. Clustering bleibt erhalten und übernimmt eine doppelte Rolle (Voraussetzung für ARIMA, Diagnose-Schicht für AE). Würzburg als Default bis PLZ-Lieferung.*
