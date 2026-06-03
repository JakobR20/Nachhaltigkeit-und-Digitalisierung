# Paper-Outline — Gesamtgliederung

> Skelett für das wissenschaftliche Paper im Modul „Nachhaltigkeit und Digitalisierung"
> (Prof. Dr. M. Müßig, FIW THWS). Autoren: Felix Zorn, Jakob Ringel.
> Zielumfang **~3000 Wörter**, max. 12 Seiten gesamt, ~8 Seiten Haupttext.
> **Dieses Skelett ist die Quelle für die spätere Poster-Ableitung** — klare
> Kapitelblöcke hier = klare Poster-Spalten später.

---

## 1. Wortbudget pro Kapitel

| Datei | Kapitel | Wortbudget |
|---|---|---|
| `01_einleitung.md` | Einleitung | ~400 |
| `02_stand_der_technik.md` | Stand der Technik | ~600 |
| `03_methodik.md` | Methodik | ~1000 |
| `04_ergebnisse.md` | Ergebnisse | ~700 |
| `05_diskussion.md` | Diskussion | ~500 |
| `06_fazit.md` | Fazit | ~150 |
| — | **Summe Haupttext** | **~3350** |
| — | (optional) Abstract ~150 vorab; Puffer durch Kürzen | — |

> Hinweis: Summe liegt knapp über 3000 — beim Ausschreiben Methodik/Ergebnisse
> straffen. THWS-Skill empfiehlt zusätzlich ein **Abstract (~150 W)** und einen
> expliziten **Forschungsfrage-+-Beitrag**-Absatz in der Einleitung (siehe
> `01_einleitung.md`). Müßig honoriert eine **Nachhaltigkeit↔Digitalisierung**-Verknüpfung
> und **SDG-Bezug** (SDG 7, SDG 9) — als Querschnitt in Einleitung/Diskussion einweben,
> Stuermer (2019) als theoretischer Anker (siehe CLAUDE.md §3).

---

## 2. Tabellen-Index (welche Tabelle in welches Kapitel)

| Artefakt | Inhalt | Zielkapitel |
|---|---|---|
| `reports/tables/06_method_comparison.md` | Vier-Methoden-Vergleich: Flag-Rate, κ, Wall-Time, Precision, Stärke/Schwäche | **04 Ergebnisse** (Kerntabelle); Methodik referenziert sie |
| `reports/tables/06_sweep_flag_rates.csv` | Flag-Rate je Methode über `threshold_pct ∈ {0; 0,1; 0,25; 0,5; 0,75}` | **04 Ergebnisse** (X-Sweep) |
| `reports/tables/07_llm_evaluation.md` | Qualitative LLM-Bewertung (Phase 5, `quality_label`) | **04 Ergebnisse** (sobald Felix+Jakob bewertet haben — aktuell noch leer) |
| methodology.md, Abschnitt „Pipeline-Lauf (Phase 4)" → Konfidenz-Tabelle pro Methode | LLM-Konfidenz mean/min–max je Methode | **04 Ergebnisse** (LLM-Statistik) |

## 3. Plot-Index (welcher Plot in welches Kapitel)

| Artefakt | Inhalt | Zielkapitel |
|---|---|---|
| `reports/figures/06_kappa_heatmap.png` | κ-Heatmap der 4 Methoden über den Sweep | **04 Ergebnisse** (Komplementarität) |
| `reports/figures/06_sweep_flag_rates.png` | Flag-Rate-Verlauf über `threshold_pct` | **04 Ergebnisse** (X-Sweep) |
| `reports/figures/05_smoke_anomalien_je_methode.png` | Beispiel-Anomalien je Methode (Lastgang) | **03 Methodik** (Methodenillustration) oder Poster-Eyecatcher |
| `reports/figures/04_silhouette_tagesprofile.png`, `04_silhouette_segment_*.png` | Silhouette-Scores Tagesprofil-/Segment-Clustering | **03 Methodik** (Cluster-Setup), bei Platzmangel Anhang |
| `reports/figures/04_segment_mean_verteilung.png` | Verteilung Segment-Mittelwerte | **03 Methodik** (Diagnose-Schicht) |
| `reports/annotation/plot_{001..066}.png` | Einzelne annotierte Anomalie-Kandidaten (66) | **03/04** als Einzelbeispiel; ein Beispiel-Plot für Poster |
| *(noch zu erzeugen)* ARIMA-Forecast + Konfidenzband + markierte Anomalie | Erklärbarkeits-Eyecatcher | **Poster** (zentral), optional 04 |

> Abbildungs-Konvention (THWS-Skill): PNG, mind. 1500 px Breite, Achsen mit Einheit,
> Quelle „Eigene Darstellung", im Text mit „siehe Abb. N" referenzieren.

---

## 4. Termin-Plan

| Datum | Meilenstein |
|---|---|
| **16.06.2026** | Poster-Entwurf (aus diesem Skelett abgeleitet) |
| **03.07.2026** | Poster final |
| **11.07.2026** | Paper final |

Ableitungslogik: Paper-Skelett (jetzt) → Poster-Blöcke (16.06., 3-Spalten:
Problem/Frage · Ansatz+Pipeline · Ergebnis/Nachhaltigkeit) → Poster final (03.07.)
→ Paper-Fließtext final (11.07.).

---

## 5. Zitations-Konvention

- **Zentrale Bibliographie:** `paper/references.bib` — einzige Quelle für alle Referenzen.
  Keine Inline-URLs im Fließtext; alles über BibTeX-Keys.
- **Stil:** APA (THWS-Vorgabe), umgesetzt über Author-Year. BibTeX-Keys im Schema
  `nachnamejahrkurzwort` (z. B. `chandola2009anomaly`, `cohen1960coefficient`).
- **In Markdown/Pandoc-Workflow** zitieren als `[@chandola2009anomaly]` →
  rendert „(Chandola et al., 2009)". Mehrfach: `[@cleveland1990stl; @hyndman2021forecasting]`.
- **In LaTeX** analog `\parencite{chandola2009anomaly}` (biblatex) bzw. `\citep{...}` (natbib).
- **Beispiel-Zitation (Markdown):**
  `Anomalieerkennung ist ein klassisches Survey-Thema [@chandola2009anomaly].`
- **Online-Quellen** tragen `urldate` (Abrufdatum 2026-06-03) — im Text als „(abgerufen am …)".
- Jede Abbildung mit Quellenangabe; eigene Plots „Eigene Darstellung".

In den Kapitel-Dateien sind die Zitationsstellen als Inline-Hinweise markiert,
z. B. `[hier @cleveland1990stl für STL zitieren]`.

---

## 6. Datei-Reihenfolge

`00_outline.md` (diese Datei) → `01_einleitung.md` → `02_stand_der_technik.md`
→ `03_methodik.md` → `04_ergebnisse.md` → `05_diskussion.md` → `06_fazit.md`.
