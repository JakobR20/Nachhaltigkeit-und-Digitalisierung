# DatenWerKIOS – Anomalieerkennung im Energieverbrauch

Master-Projekt im Modul "Nachhaltigkeit und Digitalisierung" (THWS / Prof. Müßig) in Kooperation mit RAUSCH Technology GmbH.

**Aufgabe:** KI-gestützte Erkennung von Verbrauchsanomalien in Smart-Meter-Daten + Konzept + Dashboard-Wireframe.

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
