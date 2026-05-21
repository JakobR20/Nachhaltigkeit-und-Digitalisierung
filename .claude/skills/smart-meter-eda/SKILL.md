---
name: smart-meter-eda
description: Standardvorgehen für die explorative Analyse von Smart-Meter-Zeitreihen. Aktiv, wenn der Nutzer EDA, Datenexploration, "schau dir die Daten an", "Datenprofil", "Verbrauchsdaten verstehen" oder ähnliches anfragt. Auch aktiv für Aufgaben rund um pandas DataFrames mit Zeitreihen-Index aus data/raw/.
---

# Smart-Meter-EDA – Pflichtchecks

Bei jeder explorativen Datenanalyse von Smart-Meter-Daten in diesem Projekt **immer in dieser Reihenfolge** vorgehen. Keine Abkürzungen.

## 1. Schema-Profil

Bevor irgendwas geplottet wird, **dokumentiere**:

- Welche **Spalten** existieren? (`df.dtypes`)
- Welche **Auflösung** hat die Zeitreihe? (Median der Diff: `df.index.to_series().diff().median()`)
- Welcher **Zeitraum** ist abgedeckt? Min/Max Timestamp.
- Wie viele **Zähler / Liegenschaften** (`meter_id.nunique()`)?
- Welcher **Wertebereich**? Verdacht auf Einheiten-Mix? (kW vs. kWh, Wh vs. kWh!)
- Welche **Zeitzone**? Naive Timestamps sind ein Riesenrisiko bei DST-Übergängen.

Schreib das Ergebnis nach `docs/konzept/datenprofil.md`.

## 2. Datenqualität

- **Missings**: Wo, wie viele, wie verteilt? Cluster oder einzeln?
- **Duplikate**: Gleicher Timestamp + meter_id mehrfach? (`df.index.duplicated().sum()`)
- **Zeit-Lücken**: Reindex auf erwartete Frequenz, dann `NaT`-Lücken zählen.
- **Negative Werte / Nullen**: Energiezähler dürfen nicht negativ rückwärts laufen. Stromzähler-Saldo darf negativ sein (Einspeisung). Erklären, was vorliegt.
- **Ausreißer auf erste Sicht**: einfacher Boxplot pro Zähler.

## 3. Saisonalitäts-Check

- **Tagesprofil**: Verbrauch nach Stunde (Mittel über alle Tage). Wochentag vs. Wochenende getrennt.
- **Wochenprofil**: Verbrauch nach Wochentag.
- **Jahresprofil**: Falls Daten über mehr als 4 Monate gehen, monatliche Aggregate.
- **Autokorrelation**: `statsmodels.tsa.stattools.acf(s, nlags=168)` – Spitze bei lag=24 und 168 ist gesund.

## 4. Erste Sichtkontrolle

- **Time-Series-Plot** mit niedriger Linienstärke (`linewidth=0.5`), sonst sieht man nichts.
- **Calendar-Heatmap** (Wochentag × Stunde): zeigt typisches Muster in einem Bild.
- Wenn mehrere Zähler: **Profile-Cluster** mit k-Means auf normalisierten Tagesprofilen, danach ein Plot pro Cluster.

## 5. Was nach der EDA klar sein muss

Bevor du zum nächsten Schritt (Methodenwahl) übergehst, beantworte explizit:

1. Sind die Daten sauber genug für einfache Methoden (Z-Score), oder brauchen wir erst Preprocessing?
2. Welche **Saisonalität** ist dominant (täglich, wöchentlich, jährlich)?
3. Gibt es offensichtliche **Anomalien mit bloßem Auge**, die wir später als "ground truth lite" nutzen können?
4. Welche **externen Features** versprechen Mehrwert (Temperatur ja/nein, Preis ja/nein, Kalender ja)?

## Plotting-Standard

Jeder Plot in diesem Projekt hat:
- Titel
- Achsenbeschriftung **mit Einheit** (kWh, °C, €/MWh, Stunde, ...)
- Legende, wenn mehr als eine Linie
- Niedrige Linienstärke bei dichten Zeitreihen
- `plt.tight_layout()` zum Schluss

Speichere wichtige Plots als PNG in `docs/konzept/abbildungen/` mit beschreibendem Namen, damit sie in die Hausarbeit übernommen werden können.
