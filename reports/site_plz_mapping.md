# Standort-Zuordnung: frozen-ID → PLZ (verifiziert)

Die RLM-Exporte wurden mit PLZ im Dateinamen neu geliefert (gleiche Messdaten, nur
umbenannt). `load_category` vergab dafür neue, hochgezählte meter_ids (Baumarkt_27–50),
disjunkt zu den eingefrorenen Analyse-IDs (03, 05–26). Die folgende Zuordnung wurde
**nicht** über die automatische meter_id gebildet, sondern über einen **Inhalts-
Fingerprint**: Jede neue 15-min-Datei wurde auf Stundenmittel aggregiert und gegen die
eingefrorene `features.parquet` (ebenfalls stündlich) exakt verglichen. Alle 23 frozen-
Sites matchen mit Anteil **1.000** bei klarem Abstand zum Zweitbesten (≤ 0.18).

PLZ-Centroid → lat/lon via `pgeocode` (GeoNames). Würzburg-Default ist entfallen.

| frozen-ID | PLZ | Ort | lat | lon | BL | neue Datei (meter_id) |
|-----------|-----|-----|-----|-----|----|----|
| Baumarkt_03 | 99610 | Sömmerda | 51.1369 | 11.1973 | TH | Baumarkt_29 |
| Baumarkt_05 | 17291 | Schönfeld | 53.3132 | 13.9322 | BB | Baumarkt_31 |
| Baumarkt_06 | 25899 | Bosbüll | 54.7772 | 8.8083 | SH | Baumarkt_32 |
| Baumarkt_07 | 25899 | Bosbüll | 54.7772 | 8.8083 | SH | Baumarkt_33 |
| Baumarkt_08 | 24392 | Brebel | 54.6394 | 9.7968 | SH | Baumarkt_34 |
| Baumarkt_09 | 23769 | Fehmarn | 54.4378 | 11.1935 | SH | Baumarkt_35 |
| Baumarkt_10 | 32107 | Bad Salzuflen | 52.0613 | 8.7341 | NW | Baumarkt_36 |
| Baumarkt_11 | 25813 | Husum | 54.4577 | 9.0619 | SH | Baumarkt_37 |
| Baumarkt_12 | 23730 | Sierksdorf | 54.1101 | 10.8245 | SH | Baumarkt_38 |
| Baumarkt_13 | 17367 | Eggesin | 53.6797 | 14.0799 | MV | Baumarkt_39 |
| Baumarkt_14 | 33378 | Rheda-Wiedenbrück | 51.8497 | 8.3002 | NW | Baumarkt_40 |
| Baumarkt_15 | 17192 | Varchentin | 53.5469 | 12.7743 | MV | Baumarkt_41 |
| Baumarkt_16 | 18233 | Rakow | 54.0108 | 11.6844 | MV | Baumarkt_42 |
| Baumarkt_17 | 21684 | Stade | 53.5804 | 9.5076 | NI | Baumarkt_43 |
| Baumarkt_18 | 18233 | Rakow | 54.0108 | 11.6844 | MV | Baumarkt_42 |
| Baumarkt_19 | 24852 | Süderhackstedt | 54.6042 | 9.3375 | SH | Baumarkt_44 |
| Baumarkt_20 | 23730 | Sierksdorf | 54.1101 | 10.8245 | SH | Baumarkt_45 |
| Baumarkt_21 | 23730 | Sierksdorf | 54.1101 | 10.8245 | SH | Baumarkt_45 |
| Baumarkt_22 | 18198 | Kritzmow | 54.0468 | 12.0382 | MV | Baumarkt_46 |
| Baumarkt_23 | 26723 | Emden | 53.3667 | 7.2167 | NI | Baumarkt_47 |
| Baumarkt_24 | 24109 | Melsdorf | 54.3186 | 10.0421 | SH | Baumarkt_48 |
| Baumarkt_25 | 19230 | Bandenitz | 53.4146 | 11.2253 | MV | Baumarkt_49 |
| Baumarkt_26 | 24119 | Kronshagen | 54.3333 | 10.0833 | SH | Baumarkt_50 |

## Befunde / Auffälligkeiten

- **Baumarkt_04** ist nicht Teil des frozen-Sets (nie in `features.parquet`); die
  zugehörige neue Datei `Baumarkt_30` (PLZ 24848) bleibt unbenutzt, ebenso `Baumarkt_27`
  (01) und `Baumarkt_28` (02).
- **Baumarkt_16 ≡ 18** und **Baumarkt_20 ≡ 21** sind byte-identische Zeitreihen im
  frozen-Set (overlap 26281/26281, identisch 1.0000). Sie teilen sich korrekt je eine
  PLZ-Datei (18233 bzw. 23730). Das ist eine Eigenschaft der eingefrorenen Daten und
  wird nicht verändert.
- Alle Standorte liegen in Nord-/Ostdeutschland (SH/MV/NI/NW/BB/TH); der bisherige
  Würzburg-Default (BY) lag klimatisch deutlich daneben.

## Konsequenz für die Pipeline

- Wetterunabhängig und damit **unverändert**: Anomalie-Set (66), κ, Ensemble-Coverage,
  Magnitude (+807 % Beispiel). Die Detektion nutzt kein Wetter.
- **Neu gezogen**: Wetter je Standort (`weather_by_site.parquet`) und die LLM-Schicht
  (`reports/llm_recommendations*`), die das standortgenaue Wetter konsumiert.
