---
description: Holt Wetter- und Strompreisdaten für den Zeitraum der vorhandenen Smart-Meter-Daten
---

# Aufgabe

Hole die externen Kontextdaten (Wetter, Strompreise) passend zum Zeitraum unserer Smart-Meter-Daten:

1. Bestimme aus den Smart-Meter-Daten in `data/raw/` den **Min- und Max-Timestamp**.
2. Lade DWD-Wetter via `src.apis.get_weather(lat, lon, start, end)`. Lat/Lon aus `.env` (Default Würzburg). Falls die Liegenschaften woanders sind, **frag mich nach den Koordinaten**, statt zu raten.
3. Lade EPEX-Preise via `src.apis.get_prices(start, end)`. Standard-Gebotszone DE-LU.
4. Speichere beide DataFrames als Parquet unter `data/processed/`:
   - `weather.parquet`
   - `prices.parquet`
5. Erzeuge einen kurzen Sanity-Check: Anzahl Zeilen, Min/Max-Werte, Lücken.
6. Berichte mir das Ergebnis in 5 Zeilen.

Beachte den Skill `external-data-apis`: Cache nutzen, Zeitzonen normalisieren, niemals committen.
