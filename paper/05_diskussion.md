# 5 Diskussion

> Wortbudget **~500**. Eigenständige Bewertung statt Hype; Grenzen offen benennen
> (Müßig honoriert das). Trade-offs und Risiken.

## 5.1 Hauptbefund: Ensemble statt Method-Winner (~150 W)

- Kein Sieger: κ ≈ 0 über alle 6 Paare (max 0,11) + 100 % Precision auf den Top-Kandidaten
  → die Methoden detektieren **disjunkte** Anomalie-Mengen, jede plausibel.
- `recommend_strategy` qualifiziert mehrere Methoden (Precision ≥ 0,90 UND max κ ≤ 0,40)
  → **Union-Ensemble** als Default: summiert komplementäres statt redundantes Wissen,
  niedrige False-Negative-Rate, je Flag ein Review.
- Trade-off **Union vs. Voting** benennen: Voting (≥2/4) liefe bei κ ≈ 0 fast leer →
  Union ist die richtige Default-Wahl für ein Review-Dashboard. [methodology.md „Strategie-Empfehlung"]
- Ehrlich: AE-Precision noch ausstehend → Aussage gilt sicher für 3 Methoden, AE erwartbar
  vierter Qualifier.

## 5.2 Mehrwert der LLM-Schicht (~100 W)

- LLM überführt rohen Anomalie-Score in **strukturierte, schema-validierte
  Handlungsempfehlung** unter deterministisch berechnetem Kontext (Wetter, Strompreis,
  Mehrkosten) — Zahlen kommen aus dem Code, nicht aus dem Modell.
- 0 % Schema-Fehler zeigt Praxistauglichkeit der Grammatik+Pydantic-Garantie.
- Datenschutz/Nachhaltigkeit: **lokales** LLM, kein Cloud-Abfluss, kein Trainings-Energieverbrauch
  (Stuermer Perspektive 1, „sustainability of digitalization", CLAUDE.md §3). [SDG 7/9, Müßig]

## 5.3 Limitationen (~180 W)

- **HVAC/Beleuchtung als Default-Hypothese:** Das LLM schlägt bei mehrdeutigen Anomalien
  erfahrungsbasiert HVAC-/Beleuchtungsfehler vor — als **Prüf-Aufträge ans
  Facility-Management** zu lesen, nicht als verifizierte Diagnose. Vor-Ort-Verifizierung
  nicht möglich. [methodology.md Phase 4, Limitation]
- **Wetter zentralisiert:** Würzburg-Referenz für alle Sites (Site-PLZ fehlen) → regionale
  Wetter-/Feiertagsunterschiede nicht abgebildet; Sensitivität diskutieren. [v4 §1.4]
- **Quality-Bewertung der LLM-Empfehlungen:** Eine systematische quantitative
  Quality-Bewertung der einzelnen Empfehlungen wurde nicht durchgeführt. Die Plausibilität
  wurde qualitativ durch die Autoren geprüft. Eine quantitative Bewertung über strukturierte
  Reviewer-Skalen wäre ein sinnvoller Folge-Schritt.
- **Precision nur auf stärksten Kandidaten**, keine False-Negative-Rate (Annotations-Budget).
- **Übertragbarkeit nur innerhalb Kategorie** (Baumärkte) durchgeführt; Cross-Category
  (Tankstellen/Büro) architektonisch vorgesehen, aber nicht getestet. [v4 §1.3]
- **Baumarkt_23** als Leakage-Sonderfall.

## 5.4 Übertragbarkeit und Ausblick (~70 W)

- Innerhalb-Kategorie-Generalisierung (trainieren auf N Baumärkten, anwenden auf N+1) als
  tragfähige Variante; Cross-Category als nächster Schritt.
- Weiter: Phase-5-Qualitätskennzahl ins Paper, Site-PLZ → lokale Wetterdaten,
  Ensemble-Priorisierung über Schweregrad + Überlappung.
