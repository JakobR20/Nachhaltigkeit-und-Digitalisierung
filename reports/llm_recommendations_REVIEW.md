# Qualitative Bewertung der LLM-Empfehlungen (Phase 5)

**Aufgabe:** Felix und Jakob bewerten alle 66 LLM-Empfehlungen unabhängig nach
Plausibilität und Umsetzbarkeit. Das Ergebnis fließt als Qualitäts-Kennzahl ins
Paper (Abschnitt „Evaluation der Handlungsempfehlungen").

## Wo bewerten

Datei: `reports/llm_recommendations.csv` (66 Zeilen). In Excel oder Numbers öffnen.
Die letzte Spalte **`quality_label`** ist leer und wird ausgefüllt. Alle anderen
Spalten bleiben unverändert.

> Numbers-Hinweis: nach dem Bearbeiten **als CSV exportieren** und dabei
> `reports/llm_recommendations.csv` überschreiben — sonst landen die Labels nur im
> `.numbers`-Begleitfile und nicht in der getrackten CSV (siehe Annotation-Lesson).

## Bewertungsskala (`quality_label`)

Genau einer der drei Werte pro Zeile, exakt so geschrieben:

| Wert | Bedeutung |
|---|---|
| `gut` | Plausible Hypothese **und** umsetzbare Maßnahme. |
| `akzeptabel` | Hypothese okay, aber Maßnahme vage oder nur teilweise umsetzbar. |
| `schlecht` | Hypothese falsch **oder** Maßnahme nicht umsetzbar. |

Im Zweifel die strengere Stufe wählen. Leere Zellen gelten als „noch nicht bewertet".

## Worauf sich die Bewertung stützt (alles in der CSV-Zeile)

- `vermutete_ursache` — die Hypothese des Modells
- `handlungsempfehlung_1/2/3` — die drei priorisierten Maßnahmen
- `schweregrad`, `confidence` — Selbsteinschätzung des Modells
- `site`, `timestamp`, `method`, plus über `nr` der zugehörige Plot unter
  `reports/annotation/plot_{nr:03d}.png` und das Detail-JSON unter
  `reports/llm_recommendations/{nr:03d}.json` (voller Kontext: Wetter, Preis,
  Mehrkosten) — bei Unsicherheit dort nachsehen.

## Ablauf

1. Jeder bewertet **unabhängig** alle 66 Zeilen (je ~30 s, gesamt ~30–40 min zu zweit).
   Praktisch: zwei Kopien (`_felix`, `_jakob`) oder eine zweite Spalte je Reviewer.
2. Abweichungen gemeinsam durchgehen und auf ein konsolidiertes `quality_label` einigen.
3. Die konsolidierte Fassung zurück nach `reports/llm_recommendations.csv` schreiben.
4. Auswertung erzeugen: `.venv/bin/python notebooks/_build_07_llm_evaluation.py`
   (Verteilung gut/akzeptabel/schlecht gesamt und pro Methode, Inter-Rater falls
   zwei Spalten vorhanden).

## Was die Auswertung später zeigt

- Anteil `gut` / `akzeptabel` / `schlecht` gesamt → headline-Qualitätskennzahl fürs Paper
- Aufschlüsselung pro Methode → ob bestimmte Detektoren schwerer zu erklären sind
- Querbezug zu `confidence` → ob die Modell-Konfidenz mit menschlichem Urteil korreliert
