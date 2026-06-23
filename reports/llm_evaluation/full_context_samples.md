# Full-Context-Stichproben (Phase 3, Schritt F)

Deterministische Werte, die das LLM in Phase 4 sieht. Wetter = standortgenau (DWD am Site-PLZ-Centroid), Spotpreis = Stundenwert, Mehrkosten im Code gerechnet.


| nr | method | value_kw | expected_kw | diff_kw | temp °C | Wetter | Spotpreis ct/kWh | Dauer h | Mehrkosten EUR |
|---|---|---|---|---|---|---|---|---|---|
| 19 | zscore_stl | 153.2 | 22.0 | +131.2 | -3.7 | trocken | 10.92 | 2.5 | 35.83 |
| 2 | arima | 109.4 | 19.2 | +90.2 | 6.8 | Regen | 8.79 | 2.25 | 17.83 |
| 1 | cluster_segment | 72.6 | 8.0 | +64.6 | 8.6 | trocken | 8.09 | 6 | 31.35 |
| 58 | autoencoder | 24.8 | 0.0 | +24.8 | 16.6 | Regen | -0.00 | 0.25 | 0.00 |
| 43 | cluster_segment | 49.2 | 55.8 | -6.6 | 2.4 | trocken | 11.12 | 3 | 0.00 |

## nr 19 — Baumarkt_06 · zscore_stl · vormittag

```
Anomalie-Befund:
- Standort: Baumarkt_06
- Zeitpunkt: 20.02.2026 07:30, Freitag
- Feiertag: nein
- Detektion durch: zscore_stl
- Segment: vormittag

Verbrauchs-Kontext (deterministisch berechnet, nicht vom LLM zu schätzen):
- Aktuelle Last: 153.2 kW
- Erwartete Last (Median Vergleichstage): 22.0 (Median aus 7 Vergleichstagen) kW
- Differenz: +131.2 kW = +597.2 %
- Wetter zum Anomalie-Zeitpunkt (DWD-Station nahe Standort-PLZ 25899): -3.7 °C, trocken, Niederschlag 0.0 mm, Wind 18 km/h
- Spotpreis (Stundenwert): 10.92 ct/kWh (24h-Schnitt 9.52 ct/kWh)
- Geschätzte Mehrkosten dieser Anomalie: 35.83 EUR (über ~2.5 h)

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
- Die Mehrkosten sind bereits berechnet; bei negativem Spotpreis können sie 0 oder
  negativ sein. Übernimm die Zahl, rechne sie nicht neu.
```

## nr 2 — Baumarkt_06 · arima · vormittag

```
Anomalie-Befund:
- Standort: Baumarkt_06
- Zeitpunkt: 13.01.2023 07:30, Freitag
- Feiertag: nein
- Detektion durch: arima
- Segment: vormittag

Verbrauchs-Kontext (deterministisch berechnet, nicht vom LLM zu schätzen):
- Aktuelle Last: 109.4 kW
- Erwartete Last (Median Vergleichstage): 19.2 (Median aus 1 Vergleichstagen) kW
- Differenz: +90.2 kW = +469.5 %
- Wetter zum Anomalie-Zeitpunkt (DWD-Station nahe Standort-PLZ 25899): 6.8 °C, Regen, Niederschlag 1.5 mm, Wind 32 km/h
- Spotpreis (Stundenwert): 8.79 ct/kWh (24h-Schnitt 6.98 ct/kWh)
- Geschätzte Mehrkosten dieser Anomalie: 17.83 EUR (über ~2.25 h)

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
- Die Mehrkosten sind bereits berechnet; bei negativem Spotpreis können sie 0 oder
  negativ sein. Übernimm die Zahl, rechne sie nicht neu.
```

## nr 1 — Baumarkt_03 · cluster_segment · nachts

```
Anomalie-Befund:
- Standort: Baumarkt_03
- Zeitpunkt: 08.05.2024 02:00, Mittwoch
- Feiertag: nein
- Detektion durch: cluster_segment
- Segment: nachts

Verbrauchs-Kontext (deterministisch berechnet, nicht vom LLM zu schätzen):
- Aktuelle Last: 72.6 kW
- Erwartete Last (Median Vergleichstage): 8.0 (Median aus 7 Vergleichstagen) kW
- Differenz: +64.6 kW = +807.5 %
- Wetter zum Anomalie-Zeitpunkt (DWD-Station nahe Standort-PLZ 99610): 8.6 °C, trocken, Niederschlag 0.0 mm, Wind 5 km/h
- Spotpreis (Stundenwert): 8.09 ct/kWh (24h-Schnitt 9.34 ct/kWh)
- Geschätzte Mehrkosten dieser Anomalie: 31.35 EUR (über ~6 h)

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
- Die Mehrkosten sind bereits berechnet; bei negativem Spotpreis können sie 0 oder
  negativ sein. Übernimm die Zahl, rechne sie nicht neu.
```

## nr 58 — Baumarkt_05 · autoencoder · vormittag

```
Anomalie-Befund:
- Standort: Baumarkt_05
- Zeitpunkt: 06.06.2025 10:30, Freitag
- Feiertag: nein
- Detektion durch: autoencoder
- Segment: vormittag

Verbrauchs-Kontext (deterministisch berechnet, nicht vom LLM zu schätzen):
- Aktuelle Last: 24.8 kW
- Erwartete Last (Median Vergleichstage): 0.0 (Median aus 7 Vergleichstagen) kW
- Differenz: +24.8 kW = n/a (Erwartung 0 kW, jede Last ist Abweichung) %
- Wetter zum Anomalie-Zeitpunkt (DWD-Station nahe Standort-PLZ 17291): 16.6 °C, Regen, Niederschlag 0.0 mm, Wind 22 km/h
- Spotpreis (Stundenwert): -0.00 ct/kWh (24h-Schnitt 6.07 ct/kWh)
  → Spotpreis ist negativ — Stromverbrauch wird in dieser Stunde belohnt, nicht bestraft.
- Geschätzte Mehrkosten dieser Anomalie: 0.00 EUR (über ~0.25 h)

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
- Die Mehrkosten sind bereits berechnet; bei negativem Spotpreis können sie 0 oder
  negativ sein. Übernimm die Zahl, rechne sie nicht neu.
```

## nr 43 — Baumarkt_19 · cluster_segment · mittag

```
Anomalie-Befund:
- Standort: Baumarkt_19
- Zeitpunkt: 09.02.2023 12:00, Donnerstag
- Feiertag: nein
- Detektion durch: cluster_segment
- Segment: mittag

Verbrauchs-Kontext (deterministisch berechnet, nicht vom LLM zu schätzen):
- Aktuelle Last: 49.2 kW
- Erwartete Last (Median Vergleichstage): 55.8 (Median aus 5 Vergleichstagen) kW
- Differenz: -6.6 kW = -11.9 %
- Wetter zum Anomalie-Zeitpunkt (DWD-Station nahe Standort-PLZ 24852): 2.4 °C, trocken, Niederschlag 0.0 mm, Wind 16 km/h
- Spotpreis (Stundenwert): 11.12 ct/kWh (24h-Schnitt 13.58 ct/kWh)
- Geschätzte Mehrkosten dieser Anomalie: 0.00 EUR (über ~3 h)

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
- Die Mehrkosten sind bereits berechnet; bei negativem Spotpreis können sie 0 oder
  negativ sein. Übernimm die Zahl, rechne sie nicht neu.
```
