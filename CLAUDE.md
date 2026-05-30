# CLAUDE.md
## Projekt-Basis – KI-gestützte Anomalieerkennung im Energieverbrauch

> Memory-Datei für Claude Code. Wird bei jeder Session zuerst gelesen.
>
> **Diese Datei enthält die stabilen Grundlagen** des Projekts: Kontext, Datenrealitäten, Termine, Engineering-Standards, Arbeitsweise.
>
> **Aktuelle methodische Architektur** (Methodenwahl, Cluster-Setup, LLM-Empfehlung, Übertragbarkeit) ist in **`docs/CLAUDE_patch_v4.md`** dokumentiert. Diese Datei zuerst lesen, dann v4.

---

## 1. Kontext und Stakeholder

- **Modul:** „Nachhaltigkeit und Digitalisierung" (FIW THWS, MDB-Pflichtmodul, 5 ECTS, Prof. Dr. M. Müßig)
- **Aufgabe 3 des Moduls:** KI-gestützte Anomalieerkennung im Energieverbrauch von Smart-Meter-Daten, inklusive Handlungsempfehlungen
- **Team:** Felix Zorn, Jakob Ringel (Master Digital Business, 2. Semester)
- **Industriepartner:** Rausch Technology – liefert RLM-Lastgangdaten und methodisches Feedback

---

## 2. Was gebaut wird

- **Pipeline** zur Anomalieerkennung in RLM-Lastgängen mehrerer gewerblicher Liegenschaften
- **Multi-Methoden-Vergleich** als wissenschaftlicher Ergebniskern (Details in v4)
- **Lokale LLM-basierte Handlungsempfehlung** je Anomalie
- **Streamlit-Dashboard** als operativer Vorzeigeartefakt für Rausch
- **Wissenschaftliches Paper + Visualisierung** als Modul-Prüfungsleistung

---

## 3. Theoretischer Anker für das Paper

- **Stuermer (2019), *Perspectives on Digital Sustainability*** – Verortung in „digitalization for sustainability": ICT als Enabler für Nachhaltigkeit. Anomalieerkennung macht vermeidbaren Verbrauch datengetrieben sichtbar.
- Selbstreflexive Notiz, die ins Paper gehört: die Pipeline selbst verbraucht ICT-Energie (Stuermers Perspektive 1, „sustainability of digitalization"). Lokales LLM ist hier ein bewusster Beitrag (kein Cloud-Abfluss, kein zusätzlicher Trainings-Energieverbrauch).

---

## 4. Datenrealitäten (verifiziert anhand Beispieldateien)

### 4.1 Format der RLM-Daten
- **Ein Excel-File pro Standort.** Sheet `Tabelle`, zwei Spalten.
- **Spalte 1:** Zeitstempel im Format `DD.MM.YYYY HH:MM:SS`.
- **Spalte 2:** Messwert.
- **Header-Zeile:** `Einheit | kW`. **Position der Header-Zeile ist NICHT fest** – in manchen Files Zeile 0, in anderen nach mehreren leeren Vorlaufzeilen. Loader muss die Zeile mit `Spalte0 == 'Einheit'` dynamisch suchen.
- **Einheit: kW (Leistung), nicht kWh (Energie).** Konversion: `energy_kwh = power_kw * 0.25` pro 15-min-Intervall.
- **Auflösung:** 15 Minuten. Bei 3 Jahren ergeben sich ca. 105.120 Datenpunkte pro Standort.
- **Keine Metadaten in den Files** – keine Standort-ID, keine PLZ, keine Status-Codes. Metadaten werden extern in `config/sites.yaml` gepflegt.

### 4.2 Zeitstempel und DST
- **Zeitzone:** Europe/Berlin lokal (**NICHT** UTC).
- **DST-Verhalten variiert je File:**
  - Herbst: manche Files haben duplizierte Zeitstempel (02:00–02:45 zweimal), manche überschreiben die wiederholte Stunde.
  - Frühling: 75-min-Lücke (02:00–02:45 fehlt), konsistent in allen Files.
- Loader muss tolerant gegenüber beiden DST-Varianten sein, mit klarer Log-Ausgabe pro File.

### 4.3 Zeitraum
- 01.01.2023 00:00 bis 31.12.2025 23:45 Europe/Berlin.

### 4.4 Fünf Standortkategorien
- **Tankstellen** – 24/7-Betrieb
- **Baumärkte** – begrenzte Öffnungszeit, typisch Mo–Sa
- **Ladesäulen** – Verbrauchsmuster vermutlich nachfrageabhängig, je nach Lage stark variabel
- **Büro** – Werktagsmuster, Wochenende stark abgesenkt
- **Handel** – kategoriespezifisch je nach Subbranche

Pro Kategorie ist „normal" etwas völlig anderes. Modellbildung muss kategorisierungssensitiv sein.

---

## 5. Externe Datenquellen

| Quelle | Inhalt | Auflösung | Endpunkt |
|--------|--------|-----------|----------|
| Bright Sky (DWD) | Wetter (Temperatur, Solar, Niederschlag, Wind, Cloud Cover, Humidity) | 60 min | `https://api.brightsky.dev/weather` |
| Energy-Charts | Day-Ahead-Strompreis Bidding Zone DE-LU | 60 min | `https://api.energy-charts.info/price` |
| (optional) | Stündliche CO₂-Intensität via `/public_power` | 60 min | Energy-Charts |

**Caching-Pflicht:** alle API-Antworten monatsweise als JSON unter `data/raw/<api>/<site>/<yyyy-mm>.json` persistieren. Wiederholte Pipeline-Läufe lesen aus dem Cache; Rohdaten werden nie überschrieben.

---

## 6. Projektzeitplan und Termine

| Datum | Ereignis | Status |
|-------|----------|--------|
| 26.03.2026 | Modul-Intro | ✓ |
| 16.04.2026 | Workshop mit S. Rausch im Modul | ✓ |
| 09.05.2026 | Bilateraler Rausch-Termin (Aufgabenstellung, Datenzugang) | ✓ |
| 21.05.2026 | Zwischen-Pitch | ✓ |
| 26.05.2026 | Rausch-Feedback-Termin → Architektur-Iteration (v4) | ✓ |
| 18.06.2026 | QS Methodik im Modul | offen |
| 25.06.2026 | Letzte QS im Modul | offen |
| 02.–03.07.2026 | Paper-Abgabe (1. Tag Prüfungszeitraum) | offen |

---

## 7. Prüfungsleistungen

Laut Modulhandbuch (Müßig, Foliensatz „Struktur"):
- **Wissenschaftliches Paper:** ca. 3.000 Wörter, ca. 8 Seiten Haupttext, max. 12 Seiten gesamt
- **Visualisierung:** wissenschaftliches Poster ODER Video (7–10 Min)
- Gewichtung: 50/50
- Bei Visualisierung: Content 75, Design 25

Das Streamlit-Dashboard ist **Belegmaterial** für das Paper und ein **Vorzeigeartefakt** für Rausch, aber selbst keine Prüfungsleistung.

---

## 8. Engineering-Standards

- **Sprache:** Python 3.11+
- **Dependency-Management:** `uv`, gepinnte Versionen in `pyproject.toml`
- **Lint + Format:** `ruff`
- **Type-Checks:** `mypy --strict`
- **Tests:** `pytest`, Coverage > 70 % in `src/`. **Immer mit `.venv/bin/python -m pytest` aufrufen, nie mit bloßem `python`** (s. Lesson Learned unten).
- **Logging:** strukturiert (Python-`logging`), niemals `print()` im Pipeline-Code
- **Type-Hints:** vollständig
- **Reproduzierbarkeit:** Seeds in `numpy`, `tensorflow`/`torch`, `random` fixiert
- **Konfiguration:** `config/config.yaml` als Single Source of Truth
- **Secrets:** `.env` aus `.env.example`, niemals committen

**Vertraulichkeit:** Rausch-Daten sind nicht öffentlich. `data/raw/rlm/` ist gitignored; im Repo nur synthetische Sample-Daten zur Demonstration.

**Lesson Learned (2026-05-29 / 30) – macOS-AE-Hang unter Keras 3, gelöst durch Keras-2-Pin:** Unter **TF 2.21 + Keras 3.14** hing `tf.keras.Model.fit()` auf macOS reproduzierbar in „Epoch 1/N", sobald die Trainingsdaten realistische Größenordnung erreichten (≥ 1000 Tagesfenster × 96 Slots) — in pytest wie im Standalone-Skript, mit und ohne `validation_split`/Callbacks. Synthetische 8-Fenster-Repros liefen sauber durch; der Hang war **scale-bound** und **Keras-3-spezifisch**.

**Recovery (30.05.2026, gestaffelter Plan, Stufe 1 erfolgreich):** Pin auf **TF 2.16.2 + tf-keras 2.16.0** (Keras 2 als Maintenance-Paket), aktiviert über `TF_USE_LEGACY_KERAS=1` auf Modulebene in `src/rausch_energy_anomaly/models/autoencoder.py`. Stage A (2 Sites, 1092 Fenster, epochs=30) läuft jetzt in 49,6 s; Stage C (22 Sites, Vollauf) in 68,2 s. Alle vier zuvor mit `@pytest.mark.skip` markierten fit-Tests sind grün.

**Konsequenzen:**

- Skip-Marker sind entfernt; `pytest tests/test_autoencoder.py` läuft komplett (5 passed in 8,66 s).
- AE ist **zurück im Methodenvergleich** als vierte portierte Methode; siehe `reports/methodology.md` Abschnitt „Autoencoder: Stage-A-Befund + macOS-Recovery". Notebook 06 + die Schritt-11-Tabelle müssen separat um AE erweitert werden.
- Der TF-Single-Thread-Fix (`tf.config.threading.set_intra/inter_op_parallelism_threads(1)`) steht weiterhin auf Modulebene in `autoencoder.py` und wird **nicht** in `conftest.py` dupliziert (spart 15–30 s TF-Import pro pytest-Lauf; Threading war nie die eigentliche Ursache, hilft aber unter Last).
- Der Pin ist in `pyproject.toml` unter `[project.optional-dependencies].deep` festgeschrieben; `uv sync --extra deep --extra dev` installiert die richtige Kombination.

---

## 9. Projektstruktur (Skeleton)

```
schadschoepfung-anomaly/
├── CLAUDE.md                    # diese Datei
├── docs/
│   └── CLAUDE_patch_v4.md       # aktuelle Architektur-Entscheidungen
├── README.md
├── pyproject.toml
├── .gitignore                   # data/raw/rlm/, models/*.keras, .env
├── .env.example
├── app/
│   └── dashboard.py             # Streamlit
├── config/
│   ├── config.yaml
│   ├── sites.yaml
│   └── recommendations.yaml
├── data/
│   ├── SCHEMA.md
│   ├── raw/
│   │   ├── rlm/                 # Rausch-Excels (gitignored)
│   │   ├── weather/             # Bright-Sky-Cache
│   │   └── prices/              # Energy-Charts-Cache
│   ├── interim/
│   └── processed/
├── src/schadschoepfung/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── rlm_loader.py
│   │   ├── brightsky.py
│   │   └── energy_charts.py
│   ├── preprocessing/
│   ├── features/
│   ├── models/                  # konkrete Module siehe v4
│   ├── evaluation/
│   ├── diagnosis/
│   ├── recommendations.py
│   ├── visualization/
│   └── utils/
├── notebooks/
├── tests/
├── reports/
│   ├── methodology.md
│   ├── figures/
│   └── tables/
└── models/
```

Die konkreten Module unter `src/schadschoepfung/models/` und `evaluation/` sind in **`docs/CLAUDE_patch_v4.md` Abschnitt 4** definiert.

---

## 10. Operative Arbeitsweise

**Grundregel: erst Plan, dann Code.** Pro Subtask kurzer Plan (Datenstruktur, Funktionssignatur, Testfälle) → Bestätigung im Chat → Implementierung.

**Annahmen sichtbar machen:** Bei Unsicherheit über Datenstrukturen, API-Edge-Cases oder Hyperparameter-Wahl entweder zurückfragen oder im Code-Kommentar mit `# ASSUMPTION:` markieren samt Begründung. Niemals stillschweigend annehmen.

**Beispiele für `# ASSUMPTION:`:**
- DST-Behandlung bei Files ohne Herbst-Duplikate
- Bundesland-Default für Standorte ohne explizite Region
- Schwellwert-Wahl für Anomalie-Klassifikation, wenn Validierungsdaten knapp sind

**Parallelisierung:** Die manuelle Annotation von ~200 Anomalie-Kandidaten kann ab dem Moment laufen, in dem das EDA-Notebook läuft – sie muss nicht auf trainierte Modelle warten. Das spart am Ende des Zeitplans Druck.

---

## 11. Offene Punkte (Stand 26.05.2026)

Diese Punkte sind noch nicht abschließend geklärt. Vor blockierender Implementierung Rückfrage:

1. **Postleitzahlen Baumärkte** – wird von Rausch nachgeliefert. Bis dahin gilt der Würzburg-Default (siehe v4 Abschnitt 1.4).
2. **Anschlussleistung je Standort** – falls geliefert, in `sites.yaml` ergänzen; Default `null`.
3. **Öffnungszeiten je Baumarkt** – aus den Daten ableitbar (95.-Perzentil Wochen-Lastmuster), falls nicht geliefert.
4. **CO₂-Intensität:** Default 380 g/kWh (Jahresmittel DE) oder stündlich via Energy-Charts `/public_power`. Entscheidung im Methodenkapitel.

---

## 12. Reihenfolge für Claude-Code-Sessions

**Session 1 – Setup:**
1. Diese `CLAUDE.md` lesen
2. `docs/CLAUDE_patch_v4.md` lesen
3. Repo-Skeleton anlegen (siehe Abschnitt 9)
4. `pyproject.toml` mit gepinnten Versionen schreiben
5. Im Chat antworten: Phasenplan + offene Fragen aus Abschnitt 11, BEVOR Implementierung beginnt

**Folgesessions:** gemäß Schrittfolge in **`docs/CLAUDE_patch_v4.md` Abschnitt 5**.

---

*Stand: 26.05.2026 – Projekt-Basis nach Rausch-Feedback-Termin und Zwischen-Pitch.*
