# Annotation der Top-Anomalie-Kandidaten

Felix & Jakob, bitte die ~60 Kandidaten in `annotation.csv` durchgehen und in den
beiden hinteren Spalten `label` und `notiz` füllen.

## Labels (genau einer pro Zeile)

- **`plausibel_anomal`** — sieht im Kontextfenster (±3 Tage) tatsächlich nach
  unerwartetem Verhalten aus, das eine Rückfrage beim Betreiber rechtfertigt
  (durchlaufende Nachtbasis, fehlender Tagesgang, abrupter Niveaubruch).
- **`erklärbar`** — der Ausschlag ist im Lastgang sichtbar, hat aber eine
  plausible Erklärung, die KEINE Anomalie ist (Feiertag, Wartung,
  Inbetriebnahme, Wetterspitze, Inventur).
- **`unklar`** — aus den ±3 Tagen Kontext nicht zuordenbar; im Notizfeld die
  offene Frage festhalten.

## Workflow

1. PNG zur jeweiligen `nr` öffnen (`plot_001.png` …).
2. Label in `annotation.csv` setzen, optional Notiz.
3. Bei Unsicherheit: `unklar` + Begründung in `notiz`.

## Spalten

- `nr` — laufende Nummer, korrespondiert zu `plot_{nr:03d}.png`.
- `site`, `timestamp`, `method`, `score` — Anomalie-Identifikation.
- `rang_in_methode` — Rang innerhalb der Top-20 dieser Methode (1 = höchster
  |score|). Score-Werte sind zwischen Methoden NICHT direkt vergleichbar
  (unterschiedliche Skalen) — deshalb der Rang als methoden-interner Bezug.
- `segment` — Segment des Tages (`nachts` / `vormittag` / `mittag` /
  `nachmittag`); bei Punkt-Methoden aus der Stunde abgeleitet.
- `wochentag`, `feiertag` — aus dem Zeitstempel (Feiertage Bayern).
- `also_flagged_by` — andere Methoden, die denselben `(site, timestamp)` in
  ihren Top-20 hatten (methoden-übergreifende Auffälligkeit).
- `plot_datei` — Dateiname des Kontext-Plots.
- `label`, `notiz` — **leer; wird von euch ausgefüllt.**
