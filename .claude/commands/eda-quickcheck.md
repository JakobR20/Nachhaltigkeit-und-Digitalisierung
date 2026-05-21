---
description: Führt einen schnellen EDA-Check auf einer Smart-Meter-Datei durch und schreibt das Ergebnis nach docs/konzept/datenprofil.md
---

# Aufgabe

Führe einen Quick-EDA-Check auf der Datei `$ARGUMENTS` aus `data/raw/` durch:

1. Lade die Datei mit `src.eda.load_smartmeter()`. Wenn das Schema unbekannt ist, **frag nach**, statt zu raten.
2. Erzeuge `basic_profile()` – Anzahl Zähler, Zeitraum, Auflösung, Missings.
3. Plotte für den ersten Zähler:
   - Zeitreihe (komplett)
   - Tagesprofil (Wochentag vs. Wochenende)
   - Wochenprofil
4. Schreib die Ergebnisse als Markdown nach `docs/konzept/datenprofil.md` mit:
   - Tabelle mit Profil-Zahlen
   - 3 eingebettete PNGs (gespeichert in `docs/konzept/abbildungen/`)
   - Antwort auf die 4 Fragen aus dem `smart-meter-eda`-Skill am Ende
5. Sag mir kurz, was du gemacht hast und was die wichtigste Erkenntnis ist.

Verwende den Skill `smart-meter-eda` als Leitfaden. Keine eigenen Erfindungen.
