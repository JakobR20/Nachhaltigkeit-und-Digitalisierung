# Poster-Outline – Erklärbare, übertragbare Anomalieerkennung im Energieverbrauch

> Wissenschaftliches Poster zur Aufgabe (50 % der Bewertung, Paper = andere 50 %).
> **Dies ist nur die inhaltliche Struktur/Outline – kein Layout-Design.** Visuelles Design
> (Raster, Farben, Typografie) erfolgt separat im Poster-Tool.
> Format-Annahme: A0 hochkant, klassisches 3-Spalten-Raster. Inhalte unten als Sektionen.

## Kopfzeile

- **Titel:** Erklärbare, übertragbare Anomalieerkennung im Energieverbrauch von Gewerbeliegenschaften
- Autoren: Jakob & Felix · THWS, M. Digital Business Systems
- Modul + Kooperation: Nachhaltigkeit und Digitalisierung (Prof. Müßig) · RAUSCH Technology GmbH
- Optional: QR-Code zum Repo / Prototyp

## Spalte 1 – Problem & Frage

**Sektion 1: Motivation (kurz)**
- Energiekostendruck + ESG → Verbrauchsanomalien früh erkennen.
- Smart-Meter liefern Daten, aber Rohdaten ≠ Mehrwert.

**Sektion 2: Forschungsfrage (hervorgehoben)**
- „Wie lässt sich eine erklärbare Anomalieerkennungs-Pipeline entwickeln, die (a) ohne pro-Standort-Training übertragbar ist und (b) Handlungsempfehlungen generiert?"

**Sektion 3: Datenbasis (eine Grafik)**
- 26 Baumarkt-Zähler, 15 min, kW; Saisonalität täglich + wöchentlich.
- Mini-Abbildung: Tagesprofil Werktag vs. Wochenende (aus EDA).

## Spalte 2 – Ansatz (Herzstück)

**Sektion 4: Pipeline-Diagramm (zentrale Abbildung)**
- Smart-Meter → Loader → Features (+Wetter/Preis/Kalender) → Detection → Score → LLM-Empfehlung → Dashboard.

**Sektion 5: Methodenstack (kompakt, visuell gestuft)**
- Baseline: Z-Score auf Saisonal-Residual.
- Hauptmethode: k-Means-Cluster → ARIMA pro Cluster → standardisierte Residuen = Anomalie-Score.
- Handlungsempfehlung: lokales LLM via Ollama (Qwen2.5 7B), strukturierter Output.

**Sektion 6: Kernargument (ein Eyecatcher-Plot)**
- „Warum ARIMA statt Isolation Forest": ARIMA-Vorhersage + Konfidenzband + Ist-Wert; Anomalie = Punkt außerhalb des Bandes.
- Eine Zeile: IF ignoriert Zeitstruktur; ARIMA-Residuum = Untypischkeit *für diesen Zeitpunkt* + visuell erklärbar.

## Spalte 3 – Ergebnis, Nachhaltigkeit, Fazit

**Sektion 7: Übertragbarkeit (ein Vorher/Nachher- oder Score-Verteilungs-Plot)**
- Training Baumärkte → Test ungesehene Branche ohne Nachtraining.

**Sektion 8: Dashboard-Mockup (verkleinert)**
- Übersicht-KPIs, Zeitreihe mit Konfidenzband, Anomalie-Liste mit Empfehlung.

**Sektion 9: Nachhaltigkeit & Geschäftsmodell (Icons + Stichworte)**
- SDG 7 + SDG 9; lokale DSGVO-konforme Verarbeitung als Vertrauensargument.
- Stakeholder: Betreiber, Stadtwerk/RAUSCH, KMU.

**Sektion 10: Fazit + Ausblick (knapp)**
- Erklärbarkeit als bewusste Designentscheidung; Foundation Models nur diskutiert.
- Ausblick: echte Labels, Streaming, weitere Branchen.

## Fußzeile

- Wichtigste Quellen (APA, gekürzt).
- Hinweis „Eigene Darstellung" bei eigenen Abbildungen.

---

### Abbildungs-Bedarf fürs Poster (Reuse aus `docs/konzept/abbildungen/`)
- Tagesprofil Werktag/Wochenende (vorhanden)
- Pipeline-Datenflussdiagramm (`01_datenflussdiagramm.png`, zu erstellen)
- ARIMA mit Konfidenzband + markierter Anomalie (zu erstellen)
- Score-Verteilung Train vs. Test-Branche (zu erstellen)
- Dashboard-Mockup (zu erstellen, Excalidraw)
