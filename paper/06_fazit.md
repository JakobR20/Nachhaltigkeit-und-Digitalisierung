# 6 Fazit

> Wortbudget **~150**. Drei Sätze: was gemacht, was gefunden, was als nächstes.

## Stichpunkte

- **Was gemacht:** erklärbare Pipeline auf realen RLM-Lastgängen (22+1 Baumärkte) —
  empirischer Vergleich von vier Anomalie-Methoden (Z-Score, ARIMA, Cluster-Distanz,
  Autoencoder) plus lokale LLM-Schicht (Qwen 2.5 7B) für schema-validierte
  Handlungsempfehlungen mit deterministischem Kontext.
- **Was gefunden:** kein Method-Winner (κ ≈ 0, Precision 100 % auf Top-Kandidaten) →
  **Union-Ensemble**; LLM-Pipeline 66/66 fehlerfrei, kalibrierte Konfidenz, differenzierte
  Schweregrade.
- **Was als nächstes:** qualitative LLM-Bewertung (Phase 5) abschließen, Site-PLZ für
  lokale Wetterdaten, Übertragbarkeit über Kategorien hinweg prüfen.

> Optional ein Satz Rückbindung an Forschungsfrage (Kap. 1.3) und Nachhaltigkeit
> (vermeidbarer Verbrauch sichtbar gemacht, lokales LLM ohne Cloud-Abfluss; SDG 7/9).
