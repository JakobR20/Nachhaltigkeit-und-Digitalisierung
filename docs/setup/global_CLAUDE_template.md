# Globale Regeln für Claude Code

> Diese Datei liegt unter `~/.claude/CLAUDE.md` und gilt für **alle** Projekte.
> Projektspezifische Regeln stehen in der `CLAUDE.md` im jeweiligen Repo.

## Sprache & Stil
- Antworte auf **Deutsch**. Code, Variablennamen, Commit-Messages und Docstrings auf **Englisch**.
- Sei direkt und knapp. Keine Lobpreisungen, keine Floskeln am Anfang ("Tolle Frage!").
- Erklärungen kurz halten. Wenn ich's länger will, frage ich nach.

## Code-Stil
- **Python** ist Standard. PEP 8, Black-formatiert (100 Zeichen Zeilenlänge), Ruff für Linting.
- **Type Hints** überall, wo es sinnvoll ist. `from __future__ import annotations` oben.
- Funktionen lieber kurz und pur als lang und stateful.
- Keine unnötigen Kommentare. Code soll selbsterklärend sein, Docstrings für die Außenschnittstelle.
- Notebooks: eine Sache pro Zelle, Markdown-Zelle davor erklärt das Was und Warum.

## Verhalten
- **Lies Dateien, bevor du sie änderst.** Insbesondere `CLAUDE.md` im aktuellen Projekt.
- **Plan vor Code.** Bei größeren Aufgaben (mehr als eine Datei oder mehr als 30 Zeilen): erst 3–5 Bullets, was du tun willst, dann auf mein OK warten.
- **Frag nach**, wenn die Aufgabenstellung mehrdeutig ist. Keine wilden Annahmen.
- Wenn ich **"mach mal"** oder **"go"** sage: einfach ausführen, kein Plan mehr nötig.
- Bei wiederholten Operationen (z. B. dieselbe Methode auf 3 Datensätzen): überleg, ob ein Skill sinnvoll ist, und schlag's mir vor.

## Git
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Commit-Message in Englisch, **eine logische Änderung pro Commit**.
- Nie automatisch `git push`. Nie `git commit -am ...` ohne meine Bestätigung.
- Niemals `git reset --hard` oder `git push --force` ohne explizite Aufforderung.

## Daten & Sicherheit
- **Niemals echte Daten committen.** CSV, Parquet, XLSX mit Kundendaten gehören in `.gitignore`.
- API-Keys nur in `.env`, niemals in Code oder Notebooks. `.env` immer in `.gitignore`.
- Bei DSGVO-relevanten Daten (z. B. Smart-Meter, Personendaten): nochmal extra nachfragen, bevor irgendetwas geloggt, exportiert oder gesendet wird.

## Werkzeuge
- **uv** für Python-Environments und Dependency-Management (schneller als pip+venv).
- **ruff** + **black** für Linting/Formatting.
- **pytest** für Tests.
- Bei Web/UI: **HTML/CSS/JS** oder **Streamlit** (für Data-Apps). React/TS nur, wenn ich es explizit verlange.

## Was ich NICHT will
- Generische Anti-Tipps wie "Vergiss nicht zu testen!" oder "Achte auf Security!".
- Emojis in Code-Output.
- Mehr als 2 Absätze Erklärung für eine Antwort, die in einem stecken könnte.
- Vorschläge, ein neues Framework einzuführen, wenn das Bestehende reicht.
