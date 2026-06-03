# 4 Ergebnisse

> Wortbudget **~700**. Nur Befunde, keine Wertung (die kommt in Kap. 5).
> **Anker:** `reports/tables/06_method_comparison.md`, `reports/tables/06_sweep_flag_rates.csv`,
> `reports/figures/06_*.png`, methodology.md „Methodenvergleich (Schritt 11)" + „Pipeline-Lauf (Phase 4)".

## 4.1 Methodenvergleich: Kerntabelle (~150 W)

- **Tabelle einbinden:** `reports/tables/06_method_comparison.md` (vier Methoden, Spalten:
  native Granularität, Flag-Rate Train/Test, κ vs. andere, Wall-Time fit/score, Precision,
  Stärke/Schwäche).
- Kernzahlen zum Aufgreifen:
  - Flag-Rate Test: cluster_segment 0,64 % · arima 1,05 % · autoencoder 1,21 % · zscore_stl 3,90 %.
  - Precision (3 gelabelte Methoden) je **100 %**; AE-Precision noch offen (9 Kandidaten ausstehend).

## 4.2 X-Sweep: Flag-Rate über `threshold_pct` (~120 W)

- **Plot einbinden:** `reports/figures/06_sweep_flag_rates.png`; Datenquelle
  `reports/tables/06_sweep_flag_rates.csv`.
- Befund: bei `X=0` (any) ARIMA 28,6 %, Z-Score 13,1 % → nicht haltbar. Bei **X=0,25**
  landen ARIMA (1,64×) und AE (1,89×) im 0,5×–2×-Band des Cluster-Ankers (0,64 %),
  Z-Score bleibt mit 3,90 % (6,1×) aufgebläht → **eigenständiger Befund** (Z-Score streut
  Flags breiter, kein X-Wahl-Fehler).
- **Entscheidung: X_default = 0,25** (in `config.yaml`). [methodology.md „X-Wahl"]

## 4.3 Komplementarität: κ-Heatmap (~120 W)

- **Plot einbinden:** `reports/figures/06_kappa_heatmap.png`.
- Höchster Wert **κ(arima, autoencoder) = 0,11**; alle 6 Paare **deutlich < 0,40**.
- Lesart-Hinweis (kurz, faktisch): gleiche Eingangssignale (AE+Cluster Form; Z+ARIMA Residual)
  erklären partielle Korrelation; AE wirkt als schwache Brücke zur ARIMA-Familie.
- → Methoden detektieren **disjunkte Anomalie-Mengen**.

## 4.4 Inferenzkosten (~100 W)

- Tabelle Wall-Time fit/score (aus 06_method_comparison.md): zscore ~2 ms / 0,3 ms ·
  cluster 1,4 s / 8 ms · **autoencoder 5,2 s / 3,2 s** · **arima 118,4 s / 50,1 s**.
- Paper-relevanter Befund: AE nur ~20× langsamer als Cluster, aber **~20× schneller als
  ARIMA**; Hochrechnung 22 Sites ≈ 22 s (AE) vs. ~10 min (ARIMA). Relativiert „Deep ist teuer".
- Konsequenz: nur ARIMA muss vorberechnet aus Parquet gelesen werden; AE/Z/Cluster
  on-the-fly im Dashboard möglich.

## 4.5 AE-Drift (~60 W)

- AE einzige Methode mit Test-Flag-Rate > Train (1,21 % vs. 0,89 %, Ratio 1,36) → Hinweis
  auf Site-Verhaltensdrift 2023–24 → 2025, durch pro-Site-Normierung sichtbar gemacht.
  [methodology.md „AE-Drift-Sensitivität"]

## 4.6 LLM-Pipeline-Statistik (~120 W)

- **Lauf:** 66/66 erfolgreich (100 %), **0 Retries**, **0 Schema-Fehler**; 6,6 s/Anomalie
  (warm), 8:01 min gesamt → bestätigt zweistufige Garantie (Grammatik + Pydantic).
- **Schweregrad-Verteilung:** hoch 32 / mittel 25 / niedrig 9 (kein „alles hoch"-Bias).
- **Konfidenz pro Methode** (Tabelle aus methodology.md Phase 4): AE höchste mean **0,844**
  (0,80–0,90), ARIMA niedrigste **0,818** (0,75–0,85); zscore 0,835, cluster 0,825.
  Interpretationshinweis kurz: Konfidenz des Empfehlungsmodells, nicht des Detektors.
- **Qualitative Bewertung (Phase 5):** `reports/tables/07_llm_evaluation.md` —
  **Platzhalter, `quality_label` noch leer**; sobald Felix+Jakob bewertet haben, headline
  gut/akzeptabel/schlecht hier einsetzen. [hier ggf. „n/a — ausstehend" ehrlich vermerken]
