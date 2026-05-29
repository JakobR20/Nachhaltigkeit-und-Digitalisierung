# Methodenvergleich (Schritt 11) — X_default = 0.25

Cluster-Anker (Test-Flag-Rate): 0.64%

X-Wahl-Rationale: X_default = 0.25 aus config.yaml (comparison.aggregation_threshold_pct). Methodische Entscheidung nach dem Sweep: ARIMA-Sichtbarkeit erhalten (Ratio 1,64 zum Cluster-Anker bei X=0,25). Die Z-Score/ARIMA-Asymmetrie (zscore_test 3,90 % vs. ARIMA 1,05 % vs. Cluster 0,64 % — kein gemeinsames X kalibriert beide Punkt-Methoden auf dieselbe Flag-Rate) wird als eigenständiger Befund ausgewiesen.

| Methode | Native Granularität | Flag-Rate Train | Flag-Rate Test | κ vs andere | Wall-Time fit (s) | Wall-Time score (s) | Precision | Stärke | Schwäche |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arima | point (15 min) | 1.03% | 1.05% | cluster_segment=0.02, zscore_stl=0.08 | 93.60 | 47.11 | — | Lokal-prognostische Abweichung, Peer-Gruppen-Sensitivität | Sensitiv gegen Train-Bias, langsamer |
| cluster_segment | segment_day | 1.01% | 0.64% | arima=0.02, zscore_stl=-0.01 | 0.09 | 0.01 | — | Form-/Segment-untypisch; methoden-agnostische Diagnose | Keine 15-min-Lokalisierung im Segment |
| zscore_stl | point (15 min) | 5.06% | 3.90% | arima=0.08, cluster_segment=-0.01 | 0.00 | 0.00 | — | Punkt-Outlier auf STL-Residual; transparent, schnell | Schwellwert manuell, Niveau-Drift schlecht erfasst |
