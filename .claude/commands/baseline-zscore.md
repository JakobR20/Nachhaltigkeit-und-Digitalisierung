---
description: Implementiert die Rolling-Z-Score-Baseline-Anomalieerkennung als ersten Vergleichswert
---

# Aufgabe

Baue die Baseline-Methode (Rolling Z-Score) für unser Anomalie-Vergleichssetup:

1. Schau in `src/eda/profile.py` – `rolling_zscore()` existiert schon.
2. Lege `src/anomaly/zscore.py` an mit einer Klasse `RollingZScoreDetector`, die der sklearn-style API folgt (siehe Skill `anomalie-methodenwahl`).
3. Lege `notebooks/02_baseline_zscore.ipynb` an, das:
   - Daten lädt
   - Detector auf einen exemplarischen Zähler anwendet
   - Anomalien im Zeitreihen-Plot markiert (rote Punkte)
   - Eine Liste der Top-10-Anomalien tabellarisch ausgibt
4. Plane **vor** dem Coden in 3–5 Bullets, was du tun willst, und warte auf mein OK.

Beachte: Bei Smart-Meter-Daten mit starker Saisonalität funktioniert Z-Score direkt auf dem Verbrauch schlecht – diskutiere kurz, ob du Z-Score auf den Werten oder auf den **Residuen nach STL** anwenden willst.
