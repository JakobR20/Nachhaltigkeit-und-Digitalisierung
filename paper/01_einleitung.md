# 1 Einleitung

> Wortbudget **~400**. Ton: Plural („wir analysieren"), sachlich, kein Marketing.
> Fachbegriffe beim ersten Auftreten kurz erklären.

## 1.1 Anlass und Kontext (~150 W)

- Energiewende erfordert datengetriebene Effizienz im Gewerbe; Smart-Meter-/RLM-Rollout
  schafft die Datengrundlage. [@gndew2023 für Smart-Meter-Rollout DE; @eed2023 für EU-Effizienzrahmen]
- Industrie-/Gewerbesektor als relevanter Verbrauchshebel. [@bmwk2022energieeffizienz; @bnetza2024monitoring]
- Vermeidbarer Verbrauch („Schadschöpfung") bleibt ohne Analyse unsichtbar — Anomalieerkennung
  macht ihn datengetrieben sichtbar (Stuermer-Anker: „digitalization for sustainability",
  CLAUDE.md §3).
- **Datenpartner:** Rausch Technology liefert RLM-Lastgänge von 22+1 gewerblichen Baumärkten
  (15-min-Auflösung, 2023–2026).

## 1.2 Problemstellung (~80 W)

- „Normal" ist kategorie- und standortspezifisch; keine Labels für echte Anomalien vorhanden.
- Gängige Praxis nutzt eine einzelne Methode + manuelle Sichtung; weder Methodenwahl
  empirisch begründet noch Handlungsschritt automatisiert.
- Anforderung: **erklärbar**, **ohne pro-Standort-Training übertragbar**, mit konkreter
  Handlungsempfehlung.

## 1.3 Forschungsfrage und Beitrag (~120 W)

> **Pflicht (THWS):** Forschungsfrage UND Beitrag wörtlich ausformulieren.

- **Forschungsfrage (wörtlich ausformulieren):** Lässt sich eine erklärbare Pipeline
  bauen, die (a) Anomalien im gewerblichen Lastgang ohne pro-Standort-Training findet und
  (b) je Anomalie eine strukturierte, kontextbasierte Handlungsempfehlung generiert — und
  welche Detektionsmethode (bzw. welches Ensemble) ist dafür geeignet?
- **Beitrag (wörtlich, 2–3 Sätze):**
  - Empirischer Vergleich von vier Detektionsmethoden (Z-Score, ARIMA, Cluster-Distanz,
    Autoencoder) auf realen RLM-Daten nach κ-Komplementarität, Precision, Inferenzkosten.
  - Befund: **kein Method-Winner**, daher Empfehlung eines **Union-Ensembles**.
  - Anschluss einer **lokalen LLM-Pipeline** (Qwen 2.5 7B), die je Anomalie deterministisch
    berechneten Kontext (Wetter, Strompreis, Mehrkosten) in eine schema-validierte
    Empfehlung überführt.
- Abgrenzung: kein neues Modell, sondern Integration etablierter Methoden zu einer für
  KMU-Energieanwendungen praktikablen, erklärbaren Pipeline (Lücke siehe Kapitel 2).

## 1.4 Aufbau des Papers (~50 W)

- Kapitel 2 Stand der Technik → 3 Methodik (Daten, vier Methoden, LLM) → 4 Ergebnisse
  (Methodenvergleich, LLM-Statistik) → 5 Diskussion (Ensemble-Empfehlung, Limitations)
  → 6 Fazit.
