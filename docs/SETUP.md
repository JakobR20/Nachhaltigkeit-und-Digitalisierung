# Setup-Anleitung – Schritt für Schritt

Diese Anleitung führt euch von Null bis zum vollausgestatteten Claude Code im Projekt.

> **Lesedauer:** 10 Minuten. **Setup-Zeit:** ca. 20–30 Minuten beim ersten Mal.

## Voraussetzungen

- **Python 3.11 oder neuer** – prüfen mit `python --version`
- **Node.js 18 oder neuer** – prüfen mit `node --version`
- **Git** – prüfen mit `git --version`

Falls etwas fehlt:
- Python: https://www.python.org/downloads/ oder via `pyenv`
- Node: https://nodejs.org/ (LTS-Version)
- Git: https://git-scm.com/

---

## Phase 1 – Python-Projekt aufsetzen

### 1.1 Repo initialisieren

```bash
cd ~/Projekte   # oder wo immer ihr eure Repos habt
# Falls ZIP noch nicht entpackt:
# unzip datenwerkios-anomalie.zip
cd datenwerkios-anomalie

git init
git add .
git commit -m "chore: initial project scaffold"
```

### 1.2 Python-Umgebung erstellen

**Option A – mit `uv` (empfohlen, deutlich schneller):**
```bash
# uv einmalig installieren (falls nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS/Linux
# Windows PowerShell:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

uv venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

uv pip install -e ".[dev]"
```

**Option B – mit klassischem pip:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### 1.3 Umgebungsvariablen

```bash
cp .env.example .env
```

`.env` öffnen und ggf. `DEFAULT_LAT` / `DEFAULT_LON` auf die Region der Liegenschaften anpassen. Default ist Würzburg.

### 1.4 APIs testen

```bash
python src/apis/dwd.py
python src/apis/epex.py
```

Beide sollten ein DataFrame ausgeben. Falls Fehler: Internet checken, Brightsky / energy-charts Status prüfen.

---

## Phase 2 – Claude Code installieren und konfigurieren

### 2.1 Claude Code installieren

```bash
npm install -g @anthropic-ai/claude-code
```

Beim ersten Start im Projektordner werdet ihr durch den Login geführt (Browser öffnet sich, Anthropic-Account auswählen).

### 2.2 Globale Regeln einrichten (einmalig pro Rechner)

Das ZIP enthält im Ordner `dotclaude-global/` eine **globale CLAUDE.md**. Diese gilt für **alle** zukünftigen Claude-Code-Projekte auf eurem Rechner:

```bash
# macOS/Linux:
mkdir -p ~/.claude
cp dotclaude-global/CLAUDE.md ~/.claude/CLAUDE.md

# Windows (PowerShell):
# New-Item -Type Directory -Force $env:USERPROFILE\.claude
# Copy-Item dotclaude-global\CLAUDE.md $env:USERPROFILE\.claude\CLAUDE.md
```

Was darin steht: Sprache (Deutsch antworten, Code Englisch), Code-Stil (Python/PEP8/Black/Type Hints), Git-Konventionen (Conventional Commits), Verhaltensregeln (Plan vor Code, Dateien lesen vor Änderungen). Anpassen, wenn ihr andere Vorlieben habt.

### 2.3 Plugins installieren

Claude Code starten:
```bash
claude
```

Im Claude-Code-Prompt diese drei Plugins installieren:

```
/plugin install superpowers@claude-plugins-official
/plugin install skill-creator@claude-plugins-official
/plugin install frontend-design@claude-plugins-official
```

**Was die machen:**

| Plugin | Nutzen für uns |
|--------|----------------|
| **Superpowers** | Zwingt Claude, vor jeder größeren Aufgabe einen Plan zu machen und Tests zu schreiben. Macht aus "Vibe-Coding" strukturierte Arbeit. Slash-Commands wie `/superpowers:brainstorming` und `/superpowers:systematic-debugging`. |
| **Skill Creator** | Meta-Skill zum Erstellen eigener Skills. Nützlich, wenn ihr beim Arbeiten merkt: "Das hier mach ich zum dritten Mal gleich" → daraus wird ein Skill. |
| **Frontend Design** | Greift erst, wenn wir das Streamlit-Dashboard bauen. 67 Design-Stile, vermeidet generischen AI-Look. |

Nach der Installation: **Claude Code neu starten** (mit `exit`, dann wieder `claude`).

### 2.4 Plugins verifizieren

```
/plugin
```

Sollte alle drei als installiert anzeigen.

---

## Phase 3 – Daten ablegen und loslegen

### 3.1 Smart-Meter-Daten kopieren

Die Daten aus dem OneDrive von Marja Wahl nach `data/raw/` kopieren. **Nicht committen** (bereits in `.gitignore`).

Format prüfen mit:
```bash
ls -lh data/raw/
file data/raw/*    # zeigt CSV/Parquet/etc.
```

### 3.2 Erster Lauf mit Claude Code

```bash
claude
```

Beim Start liest Claude automatisch:
1. `~/.claude/CLAUDE.md` (eure globalen Regeln)
2. `./CLAUDE.md` (Projektregeln)
3. Skills aus `.claude/skills/` (passend zum Kontext)

**Erste empfohlene Prompts:**

```
Lies CLAUDE.md im Projekt und sag mir in 5 Sätzen,
was du als deine Aufgabe verstehst.

/eda-quickcheck DATEINAME.csv

/fetch-context

/baseline-zscore
```

Die `/eda-quickcheck`-Befehle sind projektspezifische **Slash-Commands**, die im ZIP unter `.claude/commands/` mitkommen.

---

## Phase 4 – Wenn ihr Lust auf mehr habt

### Optional 4.1 – Session-Handoff für Multi-Session-Projekte

Bei Master-Projekten arbeitet man oft über Tage/Wochen. Damit Claude beim nächsten Mal nicht von vorne anfängt:

```bash
mkdir -p ~/.claude/skills/session-handoff
# Skill-Markdown von https://session.skaile.de holen
# in ~/.claude/skills/session-handoff/SKILL.md ablegen
```

Dann am Ende jeder Session: "Erstelle einen Session-Handoff."

### Optional 4.2 – Eigene Skills bauen

Wenn ihr während der Arbeit merkt "Das hier wiederhole ich oft":

```
/skill-creator:skill-creator
```

Beschreibt, was der Skill machen soll, Claude baut das `SKILL.md` mit korrektem Frontmatter.

### Optional 4.3 – Streamlit-Dashboard

Für das interaktive Wireframe:

```bash
uv pip install -e ".[dashboard]"
streamlit run src/viz/dashboard.py    # gibt's noch nicht, baut Claude bei Bedarf
```

---

## Übersicht: Wo liegt was?

| Was | Wo | Wann angepasst |
|------|-----|----------------|
| **Globale Regeln** (Sprache, Stil, Verhalten) | `~/.claude/CLAUDE.md` | Einmal pro Rechner |
| **Projekt-Regeln** (Stack, Methoden, Aufgabe) | `./CLAUDE.md` | Pro Projekt |
| **Projekt-Skills** | `./.claude/skills/<name>/SKILL.md` | Wenn Wissen kodifiziert werden soll |
| **Slash-Commands** | `./.claude/commands/<name>.md` | Wenn Multi-Step-Workflows wiederholt werden |
| **Plugins** | systemweit installiert | Einmal pro Rechner |

---

## Häufige Stolpersteine

**`ModuleNotFoundError: No module named 'src'`**
→ `pip install -e .` vergessen, oder venv nicht aktiviert.

**DWD-API liefert leeres DataFrame**
→ Brightsky hat manche Zeiträume nicht, oder Koordinaten außerhalb DE. Anderen Zeitraum probieren.

**`claude` Command not found**
→ Node.js nicht installiert oder npm-Globals-Pfad nicht in `PATH`.

**Claude Code lädt die Skills nicht**
→ Frontmatter prüfen: `---` am Anfang und Ende, valides YAML. `description` muss aussagekräftig sein, sonst triggert der Skill nicht.

**"Du hast Datei XY geändert, ohne sie zu lesen"**
→ Globale CLAUDE.md greift. Gut so. Mit "Lies vorher XY und dann mach Z" arbeiten.

**Plugin-Installation hängt**
→ `Ctrl+C`, dann `claude --version` prüfen. Bei sehr alter Version: `npm install -g @anthropic-ai/claude-code@latest`.
