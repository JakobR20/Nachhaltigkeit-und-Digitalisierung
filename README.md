# rausch-energy-anomaly – Anomalieerkennung im Energieverbrauch

Master-Projekt im Modul "Nachhaltigkeit und Digitalisierung" (THWS / Prof. Müßig) in Kooperation mit RAUSCH Technology GmbH.

**Aufgabe:** KI-gestützte Erkennung von Verbrauchsanomalien in RLM-Lastgängen + Handlungsempfehlungen + Streamlit-Dashboard; Prüfungsleistung ist Paper + Visualisierung.

**Architektur:** empirischer Vergleich dreier Methoden — Z-Score-Baseline, ARIMA pro Cluster, Autoencoder (Dense+LSTM) pro Kategorie — plus lokale LLM-Empfehlung (qwen2.5:7b via Ollama). Python-Paket: `rausch_energy_anomaly` (`src/`-Layout).

> Projektgrundlagen in `CLAUDE.md`, aktuelle Architektur in `docs/CLAUDE_patch_v4.md`.

## Setup

### 1. Python-Umgebung

```bash
# Wir empfehlen uv (schnell). Alternativ pip + venv.
# uv installieren: https://docs.astral.sh/uv/

uv venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows PowerShell

uv pip install -e ".[dev]"
```

Alternativ mit pip:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. API-Keys / Umgebungsvariablen

```bash
cp .env.example .env
```

`.env` bearbeiten falls nötig (DWD und energy-charts brauchen keinen Key, sind aber rate-limited).

### 3. Daten ablegen

Smart-Meter-Daten aus dem OneDrive von Marja Wahl nach `data/raw/` kopieren.
**Nicht committen!** Bereits in `.gitignore`.

### 4. Claude Code starten

```bash
# Einmalig installieren (Node.js 18+ benötigt):
npm install -g @anthropic-ai/claude-code

# Im Projektordner starten:
claude
```

Claude liest beim Start automatisch `CLAUDE.md` und kennt damit Aufgabe, Daten und Methodenplan.

### 5. LLM-Pipeline (Ollama)

Die Handlungsempfehlungen werden von einem **lokal laufenden** LLM erzeugt — kein Cloud-Abfluss, keine API-Keys. Produktions-Modell ist `qwen2.5:7b`.

```bash
# Ollama installieren (macOS/Linux):
curl -fsSL https://ollama.com/install.sh | sh

# Modell pullen (~5 GB Download):
ollama pull qwen2.5:7b

# Server starten (eigenes Terminal offen lassen):
ollama serve
```

**RAM-Bedarf:** ca. 5 GB für die Inferenz von `qwen2.5:7b`. Der Server lauscht standardmäßig auf `http://localhost:11434`.

> Für den optionalen Autoencoder-Vergleich wird zusätzlich TensorFlow benötigt: `uv pip install -e ".[deep]"` (gepinnt auf TF 2.16.2 + tf-keras 2.16.0, siehe `CLAUDE.md`).

### 6. Dashboard starten

Das Streamlit-Dashboard (Demo-Artefakt für Rausch) zeigt die Anomalien interaktiv über vier Seiten: **Übersicht**, **Methodenvergleich**, **Standort-Detail** (mit Hyperparameter-Slidern) und **Anomalie-Detail** (mit LLM-Empfehlung).

```bash
streamlit run app/dashboard.py
```

Öffnet automatisch `http://localhost:8501`.

- **Voraussetzungen:** `uv sync` installiert alles Nötige (Streamlit + Plotly sind enthalten). Keine API-Keys, kein Ollama nötig — das Dashboard liest vorberechnete Ergebnisse.
- **Datenstand:** Das Dashboard liest aus `data/processed/*.parquet` (Anomalie-Scores, Features) und `reports/llm_recommendations*`. Liegen diese Dateien nicht lokal vor, zeigt das Dashboard leere Tabellen — zuerst die Pipeline-Schritte laufen lassen, die die Parquets erzeugen.
- **Methoden-Farben & Branding** werden zentral in `config/dashboard.yaml` gepflegt; das Theme liegt in `.streamlit/config.toml`.

## Erste Schritte (für Claude Code)

```
> Lies CLAUDE.md und erkläre mir den Plan in eigenen Worten.

> Schau dir an, was in data/raw/ liegt, und baue notebooks/01_eda.ipynb,
  das die Datenstruktur dokumentiert.

> Implementiere den DWD-Wetter-Client in src/apis/dwd.py mit Caching.
```

## Projektstruktur

Siehe `CLAUDE.md` – dort ist die Verzeichnisstruktur und der Methodenkanon dokumentiert.

## Ansprechpartner

- **RAUSCH Technology:** Marja Wahl (Data Scientist)
- **Hochschule:** Prof. Dr. Michael Müßig
