---
name: paper-poster-thws
description: Konventionen für die wissenschaftliche Ausarbeitung (Paper + Poster) zum Master-Projekt im Modul "Nachhaltigkeit und Digitalisierung" an der THWS. Aktiv, wenn der Nutzer Paper, Poster, wissenschaftliche Ausarbeitung, Forschungsfrage, Abstract, Konzeptpapier, Dashboard-Skizze, Wireframe, Zitation, APA oder Schreibstil erwähnt.
---

# Paper- & Poster-Konventionen (THWS)

**Aufgabenformat:** Wissenschaftliches **Paper (~3000 Wörter, max. 12 Seiten)** + wissenschaftliches **Poster**. Gewichtung **50/50**. Der lauffähige Notebook-Prototyp ist Beleg/Bonus, nicht die Abgabe.

> Hinweis: Dieses Projekt ist von "Konzept + Wireframe" auf "Paper + Poster" umgestellt. Beides – Paper und Poster – muss eigenständig für sich funktionieren.

## Paper-Struktur (`docs/konzept/konzept.md`)

IMRaD-angelehnt, mit den THWS-Nachhaltigkeitsanforderungen integriert. Wörterbudget je Abschnitt grob planen (Summe ≈ 3000):

0. **Abstract** (~150 W) – Problem, Lücke, Beitrag, Kernergebnis in einem Absatz.
1. **Einleitung** (~350 W) – Motivation, Problemstellung, **explizite Forschungsfrage**, **expliziter Beitrag**, Abgrenzung.
2. **Stand der Forschung** (~450 W) – klassische Statistik, klassisches ML, Deep Learning/Foundation Models; Forschungslücke/Positionierung.
3. **Datenbasis** (~350 W) – Quelle, Umfang, Auflösung, Qualität (aus EDA übernehmen); externe Quellen mit Begründung.
4. **Methodischer Rahmen & Anforderungen** (~250 W) – Anomalie-Typologie, nicht-funktionale Anforderungen (Erklärbarkeit, DSGVO, Übertragbarkeit), Evaluationsstrategie.
5. **Architektur des Prototyps** (~700 W, **Kern**) – Datenfluss + die gewählten Methoden mit ausführlicher Begründung.
6. **Evaluation** (~250 W) – Vergleichslogik, Metriken (auch ohne Labels), Übertragbarkeit.
7. **Dashboard-Konzept / Wireframe** (~250 W) – Komponenten + Mockup-Verweis.
8. **Diskussion** (~250 W) – Trade-offs, Grenzen, Risiken, eigenständige Bewertung.
9. **Nachhaltigkeit & Geschäftsmodell** (~300 W) – SDG, Müßig-Dimensionen, Stakeholder.
10. **Fazit & Ausblick** (~200 W).
11. **Literatur** (APA).

**Pflicht in der Einleitung:** Forschungsfrage **und** Beitrag wörtlich ausformulieren – nicht implizit lassen.

## Poster-Struktur (`docs/poster/poster_outline.md`)

- Das Poster ist eine **eigenständige** 50-%-Leistung, keine verkleinerte Paper-Kopie.
- Annahme: A0 hochkant, 3-Spalten-Raster: **Spalte 1** Problem & Forschungsfrage, **Spalte 2** Ansatz (Pipeline-Diagramm + Kernargument als Eyecatcher), **Spalte 3** Ergebnis, Nachhaltigkeit, Fazit.
- Ein **zentraler Eyecatcher-Plot** (z. B. ARIMA-Vorhersage + Konfidenzband + markierte Anomalie) trägt das Poster.
- Outline und Layout-Design trennen: erst Inhalt/Struktur, dann visuelles Design im Tool.

## Schreibstil

- **Deutsch**, sachlich, **Plural** ("wir analysieren", nicht "ich habe").
- Fachbegriffe beim ersten Auftreten kurz erklären, dann nutzen.
- Keine Marketing-Sprache ("revolutionär", "disruptiv"). Aktive Sprache, kurze Sätze.
- Wissenschaftlicher Ton: Behauptungen belegen oder als Annahme kennzeichnen; Grenzen offen benennen.

## Zitation

- **APA-Style**, durchgehend. (Müßigs Kürzel-System aus dem Skript NICHT übernehmen – vollständig APA.)
- Online-Quellen mit **Abrufdatum**.
- Jede Abbildung mit Quelle, eigene als "Eigene Darstellung".

## Abbildungen

- Speicherort: `docs/konzept/abbildungen/`. Format PNG, **mind. 1500 px** Breite (Druck/Poster).
- Dateinamen nummeriert + beschreibend: `01_datenflussdiagramm.png`, `02_tagesprofil_typischer_zaehler.png`, …
- Im Text **referenzieren** ("siehe Abb. 3"). Plot-Standard wie im Projekt: Titel, Achsen **mit Einheit**, Legende, niedrige Linienstärke bei dichten Reihen.

## Dashboard-Wireframe (fürs Paper + Poster)

Mindestkomponenten:
- **Übersichtskarte:** KPIs (Anomalien letzte 7 Tage, betroffene Zähler, geschätzter Mehrverbrauch in kWh).
- **Zeitreihen-Panel:** Verbrauch mit ARIMA-Erwartung + Konfidenzband + hervorgehobenen Anomalien (zentrales Erklärbarkeitsbild).
- **Anomalie-Liste:** Timestamp, Zähler, Schweregrad, vorgeschlagene Handlung (LLM).
- **Drilldown:** Kontext (Wetter, Preis, Tagesprofil-Abweichung).
- **Filter:** Zeitraum, Zähler, Anomalie-Typ.
- Statischer Mockup (Pflicht, z. B. Excalidraw → PNG); interaktive Streamlit-Variante (`src/viz/dashboard.py`) optional, max. 1 Tag Aufwand.

## Müßigs Bewertungslogik (Erfahrungswerte)

Besonders honoriert:
- Klare **Verknüpfung Nachhaltigkeit ↔ Digitalisierung** – nicht nur "wir bauen ein KI-Modell".
- **Geschäftsmodell-Dimension** (Stakeholder-Sicht, Business Model Canvas).
- **Eigenständige Bewertung** der Grenzen statt Hype.
- **8 Dimensionen der Nachhaltigkeit** (Vogt) als Reflexionsraster, wo passend.
- **SDG-Bezug** (v. a. SDG 7 – bezahlbare/saubere Energie, SDG 9 – Innovation).

## Projektspezifische inhaltliche Leitplanken

- **Erklärbarkeit** ist das nicht-funktionale Leitmotiv: Foundation Models (Chronos, TimeRCD, TranAD, THEMIS) nur **diskutieren**, nicht implementieren.
- **Forschungsfrage** (Stand Mai 2026): erklärbare Pipeline, die (a) ohne pro-Standort-Training übertragbar ist und (b) Handlungsempfehlungen generiert.
- Architektur-Details und Methodenbegründung: siehe Skill `anomalie-methodenwahl`.
