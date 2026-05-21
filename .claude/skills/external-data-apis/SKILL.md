---
name: external-data-apis
description: Konventionen für API-Calls zu externen Datenquellen in diesem Projekt (DWD-Wetter via Brightsky, EPEX-SPOT-Preise via energy-charts). Aktiv, wenn der Nutzer Wetterdaten, Strompreise, externe Datenquellen, API-Calls, Caching, DWD, Brightsky, EPEX, energy-charts oder Feature-Engineering mit externen Daten erwähnt.
---

# External Data APIs – Konventionen

Wir nutzen zwei externe APIs:

| Quelle | Was | Endpoint | Authentifizierung |
|--------|-----|----------|--------------------|
| **DWD** via Brightsky | Wetter (Temperatur, Strahlung, Wind) | `https://api.brightsky.dev/weather` | Keine |
| **energy-charts** (Fraunhofer ISE) | EPEX-SPOT Day-Ahead-Preise | `https://api.energy-charts.info/price` | Keine |

Beide Clients liegen in `src/apis/`. **Nicht neu schreiben** – nutze `get_weather()` und `get_prices()`.

## Pflicht-Pattern für API-Calls

Jeder neue API-Call in diesem Repo muss:

1. **Cachen.** Antworten landen unter `data/external/<api>/<sinnvoller-key>.json`. Bei Re-Run wird der Cache genutzt, nicht die API. Cache-Invalidierung manuell (Datei löschen) – kein automatisches TTL nötig.
2. **Retries** mit Exponential Backoff via `tenacity`. 3 Versuche, 1–10 Sekunden.
3. **Timeout** von 30 s. Niemals ohne Timeout.
4. **Logging** auf INFO-Level: "X aus Cache" oder "X von API geholt".
5. **Saubere DataFrames** zurückgeben: tz-aware Timestamp-Index in UTC, Spaltennamen lowercase mit Unterstrich.

## Anti-Patterns

- ❌ API in einer Notebook-Zelle direkt aufrufen statt `from src.apis import ...`. Wenn ein Helper fehlt → in `src/apis/` ergänzen.
- ❌ Riesige Zeiträume in einem Call (z. B. 5 Jahre Stundendaten). Lieber **in Monatsblöcken** chunken und cachen.
- ❌ Antworten in den Repo committen. `data/external/` ist in `.gitignore`.
- ❌ Bei Fehler stillschweigend leere DataFrames returnen. Lieber loggen und werfen.

## Wetter-Features für Anomalieerkennung

Aus DWD-Daten typischerweise sinnvoll als Feature:

- `temperature` (°C) – höchste Erklärkraft für Heizverbrauch
- `temperature_lag_24h`, `temperature_lag_48h` – thermische Trägheit von Gebäuden
- `solar_irradiance` (W/m²) – relevant bei PV-Beitrag
- `wind_speed` – marginal bei Gebäuden, wichtig bei PV/Wind
- `hdd` (Heating Degree Days, abgeleitet: `max(15 - temp, 0)`) – linearer Heizverbrauch-Proxy

## Preis-Features

Aus energy-charts:

- `price_eur_mwh` – Day-Ahead-Spotpreis
- `price_lag_24h` – gestern selbe Stunde (zur Erkennung preisinduzierter Lastverschiebung)
- `is_negative` – Boolean, ob Preis negativ war (Indikator für Überschuss-Erzeugung)

## Zeitzonen-Falle

- DWD und energy-charts liefern UTC.
- Smart-Meter-Daten in Deutschland sind oft in **CET/CEST** (mit DST!).
- **Vor dem Join** alle Zeitstempel auf UTC normalisieren. Nach dem Join optional auf "Europe/Berlin" zurück für Plots.
- Bei 15-Min-Daten: 02:00–03:00 am DST-Wechsel-Tag prüfen, dort entstehen sonst Geister-Rows oder NaT.

## Join-Pattern

Wetter und Preise liegen meist stündlich vor, Smart-Meter oft viertelstündlich. Standard:

```python
# Smart-Meter auf Stunden aggregieren ODER Wetter auf 15-Min vorwärts-füllen
df_h = smart_meter.resample("1h").mean()         # bei Leistung
# oder
df_h = smart_meter.resample("1h").sum()          # bei Energie
df = df_h.join(weather, how="left").join(prices, how="left")
```

Niemals `pd.merge_asof` ohne `tolerance` – sonst werden Werte über Stunden hinweg geforward-fillt.
