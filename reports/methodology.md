# Methodology (work in progress)

> Lebendes Methodenkapitel. Wird im Verlauf der Modellierungsphase gefüllt; die finale
> Methodenentscheidung fürs Dashboard wird hier nach dem Methodenvergleich (v4 §5
> Schritt 11+12) dokumentiert.

## Methodenvergleich (drei Methoden)

| Layer | Methode | Status |
|-------|---------|--------|
| Baseline | Z-Score auf STL-Residual | portiert (`models/baseline_zscore.py`) |
| Haupt A | ARIMA pro Cluster | offen |
| Haupt B | Autoencoder (Dense + LSTM) pro Kategorie | offen |

Vergleichsmetriken: geschätzte Precision (manuelle Annotation ≈ 200 Punkte), Cohen's Kappa
(Methodenübereinstimmung), Inferenzzeit pro Standort, qualitative Erklärbarkeit.

## Offene Sensitivitäts-/Limitationsdiskussionen

- **CO₂-Intensität:** Default 380 g/kWh (Jahresmittel DE) vs. stündliche Variante via
  Energy-Charts `/public_power`. Sensitivität der abgeleiteten CO₂-Aussagen hier diskutieren.
- **Würzburg-Default:** Solange Postleitzahlen fehlen, werden alle Standorte mit Würzburger
  Koordinaten/Bundesland (BY) bewettert. Sensitivität (regionale Wetterunterschiede,
  Feiertags-Bundesland) als Limitation diskutieren.
- **Übertragbarkeit:** Innerhalb-Kategorie-Generalisierung (trainieren auf N Baumärkten,
  anwenden auf einen weiteren) statt Cross-Category-Transfer (v4 §1.3).
