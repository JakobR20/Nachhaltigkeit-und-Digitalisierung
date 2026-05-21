# DatenWerKIOS – KI-gestützte Anomalieerkennung im Energieverbrauch

## Projektkontext

Dieses Projekt entsteht im Modul **"Nachhaltigkeit und Digitalisierung"** (Prof. Dr. Michael Müßig, THWS, Master Digital Business Systems) in Kooperation mit **RAUSCH Technology GmbH** (Sven Rausch).

**Bearbeitende:** Jakob und Felix
**Ansprechpartnerin bei RAUSCH:** Marja Wahl (Data Scientist)
**Cluster 2, Aufgabe 3:** KI-gestützte Anomalieerkennung im Energieverbrauch auf Basis von Smart-Meter-Daten.

## Aufgabenstellung (Originalwortlaut)

> Auf Basis von Smart-Meter-Daten sollen Verbrauchsanomalien erkannt und Handlungsempfehlungen generiert werden. Skizziert einen Prototyp-Ansatz: Welche Daten braucht ihr, welche KI-Methode nutzt ihr, wie sieht das Dashboard aus? (Kein Code nötig – Konzept + Wireframe reicht.)

**Schlagworte:** Anomalieerkennung, Smart Meter, KI, Dashboard, Energieeffizienz

**Wichtig:** Pflichtabgabe ist Konzept + Wireframe. Wir gehen **darüber hinaus** und bauen einen lauffähigen Notebook-Prototyp, weil Marja uns echte Daten und einen Methoden-Stack-Hinweis geschickt hat. Der Prototyp ist Bonus, nicht Ersatz für das Konzept.

## Was Claude Code in diesem Repo tun soll

Du bist Coding-Partner für ein Master-Projekt. Halte dich an folgende Prinzipien:

1. **Erklären statt nur liefern.** Jakob und Felix lernen das Thema neu. Wenn du eine Methode wählst (z. B. Isolation Forest statt LOF), sag in 2–3 Sätzen warum.
2. **Klein anfangen.** Wir bauen iterativ. Erst EDA, dann eine simple Baseline (Rolling Z-Score), dann ML-Methoden. Nicht direkt mit LSTM einsteigen.
3. **Reproduzierbar.** Jeder Schritt landet in einem nummerierten Notebook (`01_eda.ipynb`, `02_baseline.ipynb`, ...) oder einem Modul unter `src/`.
4. **Keine Smart-Meter-Daten ins Repo committen.** `data/raw/` ist in `.gitignore`. DSGVO-relevant.
5. **Deutsch ist OK** für Kommentare und Markdown. Variablennamen auf Englisch.
6. **Frag nach**, wenn die Aufgabenstellung mehrdeutig ist. Wir haben Zugriff auf Marja per Mail.

## Daten

### Primärdaten (von RAUSCH via OneDrive)
- Smart-Meter-Verbrauchsdaten – Schema noch zu erkunden, liegt in `data/raw/`
- Sobald Daten da sind: erste Aufgabe ist EDA-Notebook (`notebooks/01_eda.ipynb`), das beantwortet:
  - Welche Spalten? Welche Auflösung (15 min / 1 h / täglich)?
  - Welcher Zeitraum?
  - Wie viele Zähler/Liegenschaften?
  - Wie viele Missing Values? Wie sieht der Tages-/Wochen-/Saisonal-Zyklus aus?
  - Gibt es Labels für bekannte Anomalien? (Vermutlich nein → unsupervised.)

### Externe Datenquellen
- **Wetterdaten (DWD):** https://dwd.api.bund.dev/ – Temperatur, Globalstrahlung, Wind. Erwartete Korrelation: kalte Tage → höherer Verbrauch.
- **Strompreise (EPEX SPOT via energy-charts):** https://api.energy-charts.info/ – Day-Ahead-Preise. Kann erklären, ob Verbrauchsänderungen preisinduziert sind (z. B. dynamische Tarife).
- Optional später: Feiertagskalender, Schulferien (öffentliche APIs).

## Methodenkanon (aus Marjas Mail)

In etwa dieser Reihenfolge testen, von einfach nach komplex:

| Stufe | Methode | Warum |
|-------|---------|-------|
| 0 | Rolling Z-Score / IQR auf Residuen | Baseline. Schnell, erklärbar, gut fürs Konzept. |
| 1 | STL-Decomposition + Residual-Outlier | Trennt Trend/Saison/Rest. Standardansatz für Zeitreihen. |
| 2 | Isolation Forest auf Features (Stunde, Wochentag, Lag, Wetter) | Unsupervised, robust, gut interpretierbar via Feature-Importance. |
| 3 | DBSCAN / k-Means auf Tagesprofilen | Findet untypische Tage. Cluster-Bewertung mit Silhouette. |
| 4 | ARIMA / SARIMA + Prediction Interval | Statistisches Forecasting, Anomalie = Wert außerhalb Konfidenzband. |
| 5 | LSTM-Autoencoder oder Prophet | Nur wenn Zeit reicht und es Mehrwert gibt. Schwer zu erklären in der Hausarbeit. |

**Faustregel:** Für die Hausarbeit zählt Methodenvielfalt + saubere Begründung mehr als das fancyste Modell. Lieber 3 Methoden gut verglichen als ein LSTM ohne Vergleich.

## Tech-Stack

- **Python 3.11+** (via uv oder venv)
- **Pandas, NumPy** – Datenhandling
- **scikit-learn** – Isolation Forest, DBSCAN, k-Means, Preprocessing
- **statsmodels** – STL, ARIMA
- **Plotly** (interaktiv) und **Matplotlib** (statisch für Hausarbeit)
- **Streamlit** (optional) – falls wir das Wireframe-Dashboard lauffähig machen wollen
- **Jupyter** – Notebooks
- **httpx** + **tenacity** – API-Calls mit Retry
- **ruff** + **black** – Linting/Formatting

## Verzeichnisstruktur

```
datenwerkios-anomalie/
├── CLAUDE.md                  # Diese Datei
├── README.md                  # Projektbeschreibung für Menschen
├── pyproject.toml             # Dependencies
├── .env.example               # Vorlage für API-Keys
├── .gitignore
├── data/
│   ├── raw/                   # Smart-Meter-Daten (NICHT committen)
│   ├── external/              # Wetter, Preise (Cache, nicht committen)
│   └── processed/             # Cleaned / Feature-Engineered (nicht committen)
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_baseline_zscore.ipynb
│   ├── 03_stl_decomposition.ipynb
│   ├── 04_isolation_forest.ipynb
│   └── 05_method_comparison.ipynb
├── src/
│   ├── apis/                  # DWD- und Strompreis-Clients
│   ├── eda/                   # Wiederverwendbare Plot- und Stats-Helfer
│   ├── anomaly/               # Methodenimplementierungen (sklearn-style fit/predict)
│   └── viz/                   # Dashboard- und Plot-Templates
├── docs/
│   ├── konzept/               # Hausarbeit / Konzeptpapier
│   └── wireframe/             # Dashboard-Skizzen
└── tests/                     # Unit-Tests, v. a. für API-Clients
```

## Arbeitsweise mit Claude Code

- **Plan zuerst.** Bevor du Code schreibst, sag in 3–5 Bullets, was du tun willst. Dann erst die Datei.
- **Eine Sache pro Notebook-Zelle.** Lange Zellen sind unlesbar.
- **Plots haben immer:** Titel, Achsenbeschriftung, Einheit, Legende. Kein Default-Matplotlib-Style.
- **Wenn du eine API rufst:** Immer mit Caching (`data/external/`). Wir wollen nicht bei jedem Notebook-Rerun den DWD nerven.

## Projekt-Skills (.claude/skills/)

Folgende Skills werden je nach Kontext automatisch aktiv:

- **smart-meter-eda** – Pflichtchecks bei explorativer Analyse von Smart-Meter-Daten.
- **anomalie-methodenwahl** – Entscheidungslogik für die Methodenwahl (Z-Score, STL, Isolation Forest, etc.).
- **external-data-apis** – Konventionen für DWD- und EPEX-API-Calls (Caching, Retries, Zeitzonen).
- **paper-poster-thws** – Struktur, Schreibstil und Zitation für Paper (3000 Wörter) + Poster (50/50).

Wenn ein Skill nicht greift, obwohl er passt: `description`-Frontmatter überprüfen.

## Slash-Commands (.claude/commands/)

- `/eda-quickcheck <datei>` – Schneller EDA-Check mit Profil und Plots, Output nach `docs/konzept/datenprofil.md`.
- `/fetch-context` – Holt Wetter und Strompreise passend zum Datenzeitraum.
- `/baseline-zscore` – Implementiert die Z-Score-Baseline mit Notebook.
- `/sync-konzept` – Aktualisiert das Konzeptpapier auf den aktuellen Stand.

## Stand der Aufgabe

- [x] Projektstruktur angelegt
- [ ] Smart-Meter-Daten ins `data/raw/` einlesen
- [ ] EDA-Notebook (`01_eda.ipynb`)
- [ ] DWD-Wetter-Client + Cache
- [ ] EPEX-Strompreis-Client + Cache
- [ ] Baseline Z-Score
- [ ] STL-Dekomposition
- [ ] Isolation Forest mit Wetter-Features
- [ ] Methodenvergleich
- [ ] Wireframe Dashboard
- [ ] Konzeptpapier
