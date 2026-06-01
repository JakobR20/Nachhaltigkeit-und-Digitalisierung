# Prompt-Varianten-Vergleich (Schritt C)

Modell: `qwen2.5:7b` · temperature=0.2 · seed=42 · Schema grammar-erzwungen + Pydantic-validiert.

Wetter/Strompreis/Mehrkosten sind `<Phase 3>` (Kontext-Builder liefert vorerst nur Lastgang-Fakten).


## Test-Anomalien

| nr | site | timestamp | method | segment | score |
|---|---|---|---|---|---|
| 19 | Baumarkt_06 | 2026-02-20 07:30:00+01:00 | zscore_stl | vormittag | 9.62 |
| 2 | Baumarkt_06 | 2023-01-13 07:30:00+01:00 | arima | vormittag | 20.44 |
| 1 | Baumarkt_03 | 2024-05-08 02:00:00+02:00 | cluster_segment | nachts | 12.40 |
| 58 | Baumarkt_05 | 2025-06-06T10:30:00+02:00 | autoencoder | vormittag | 10.20 |
| 43 | Baumarkt_19 | 2023-02-09 12:00:00+01:00 | cluster_segment | mittag | 9.10 |

## nr 19 — Baumarkt_06 · zscore_stl · vormittag

<details><summary>User-Prompt (Kontext)</summary>

```
Anomalie-Befund:
- Standort: Baumarkt_06
- Zeitpunkt: 20.02.2026 07:30, Freitag
- Feiertag: nein
- Detektion durch: zscore_stl
- Segment: vormittag

Verbrauchs-Kontext (deterministisch berechnet):
- Aktuelle Last: 153.2 kW
- Erwartete Last (Median Vergleichstage): 22.0 (Median aus 7 Vergleichstagen) kW
- Differenz: +131.2 kW = +597.2 %
- Wetter: <Phase 3> °C, <Phase 3>
- Strompreis aktuell: <Phase 3> ct/kWh
- Geschätzte Mehrkosten dieser Anomalie: <Phase 3> EUR

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
```
</details>

| Variante | Ergebnis |
|---|---|
| V1_minimal | **hoch** · conf 0.95 · 10.0s<br>_Ursache:_ Fehler im Thermostatautomat der Heizung oder Lüftungsanlage, da die aktuelle Last weit über den normalen Betriebsbereich von 22 kW liegt.<br>_Empf.:_<br>1. Sofortige Inspektion und Überprüfung des Thermostatautomaten in der Heizung/Lüftungskonfiguration, da eine Fehlfunktion zu dieser ungewöhnlich hohen E<br>2. #123; unterbrochen für Formatierung, fortgesetzt:<br>3. Sofortige Inspektion und Überprüfung des Thermostatautomaten in der Heizung/Lüftungskonfiguration, da eine Fehlfunktion zu dieser ungewöhnlich hohen E |
| V2_fewshot | **hoch** · conf 0.85 · 6.6s<br>_Ursache:_ Ungeplante Öffnungszeiten oder ungewöhnliche Verkaufsaktivitäten (z.B. Großbestellungen, Veranstaltungen) am Freitag morgens.<br>_Empf.:_<br>1. Überprüfen der Kassen- und Verkaufsdaten für unerwartete Aktivitäten<br>2. Prüfung der Öffnungszeiten bei den Anbietern und Kunden<br>3. Wartungstermin vereinbaren, um Regelungssysteme zu überprüfen |
| V3_cot | **hoch** · conf 0.90 · 7.2s<br>_Ursache:_ Unvorhergesehene Betriebskosten durch unerwartet lange Öffnungszeiten oder technische Probleme mit dem Kühl- und Klimasystem.<br>_Empf.:_<br>1. Überprüfen Sie den Status der Kühlanlagen und HVAC-Systeme, um Unvorhergesehene Betriebskosten zu vermeiden.<br>2. Kontaktieren Sie den Lieferanten für technische Unterstützung, falls das System nicht ordnungsgemäß gesteuert wird.<br>3. Dokumentieren Sie die Anomalie und prüfen Sie die Öffnungszeiten der nächsten Tage, um unerwartete Betriebszeiten zu vermeiden. |

## nr 2 — Baumarkt_06 · arima · vormittag

<details><summary>User-Prompt (Kontext)</summary>

```
Anomalie-Befund:
- Standort: Baumarkt_06
- Zeitpunkt: 13.01.2023 07:30, Freitag
- Feiertag: nein
- Detektion durch: arima
- Segment: vormittag

Verbrauchs-Kontext (deterministisch berechnet):
- Aktuelle Last: 109.4 kW
- Erwartete Last (Median Vergleichstage): 19.2 (Median aus 1 Vergleichstagen) kW
- Differenz: +90.2 kW = +469.5 %
- Wetter: <Phase 3> °C, <Phase 3>
- Strompreis aktuell: <Phase 3> ct/kWh
- Geschätzte Mehrkosten dieser Anomalie: <Phase 3> EUR

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
```
</details>

| Variante | Ergebnis |
|---|---|
| V1_minimal | **hoch** · conf 0.95 · 7.2s<br>_Ursache:_ Fehler im Thermostatautomat der Heizung oder Lüftungsanlage, da die erwartete niedrige Last nicht eingehalten wird.<br>_Empf.:_<br>1. Sofortiges Inspectieren des Thermostatautomaten und Überprüfen der Heiz- und Lüftungsanlagen zur Identifizierung eventueller Schäden oder Fehlstellens<br>2. Überprüfung der Einstellungen im Automat, ob eine ungewöhnlich hohe Temperatur oder Luftgeschwindigkeit eingestellt ist.<br>3. Sollte die Ursache nicht sichtbar sein, wird ein Fachmann für Heizung und Lüftung gerufen, um die Anlage gründlich zu überprüfen. |
| V2_fewshot | **hoch** · conf 0.85 · 6.5s<br>_Ursache:_ Erwarming der Verkaufsfläche und Lüftung trotz geringer Kundenlast am Freitagmorgen<br>_Empf.:_<br>1. Prüfen, ob die Heizungs- und Lüftungssysteme auf den tatsächlichen Bedarf eingestellt sind<br>2. Überprüfung der Regelung des HVAC-Systems zur Optimierung der Energieverbrauchsmuster<br>3. Wartungstermin vereinbaren, um mögliche Defekte im System zu prüfen |
| V3_cot | **hoch** · conf 0.92 · 5.9s<br>_Ursache:_ Fehler im Thermostatin der Heizung oder unerwarteter Aufruf der Kühlanlage.<br>_Empf.:_<br>1. Überprüfen Sie den Thermostatin der Heizung und stellen Sie sicher, dass er korrekt eingestellt ist.<br>2. Prüfen Sie die Kühlanlagen auf mögliche Fehlermeldungen oder unerwartete Anrufe.<br>3. Verifizieren Sie die Strompreise und überprüfen Sie, ob ein Preis-Spike der Ursache ist. |

## nr 1 — Baumarkt_03 · cluster_segment · nachts

<details><summary>User-Prompt (Kontext)</summary>

```
Anomalie-Befund:
- Standort: Baumarkt_03
- Zeitpunkt: 08.05.2024 02:00, Mittwoch
- Feiertag: nein
- Detektion durch: cluster_segment
- Segment: nachts

Verbrauchs-Kontext (deterministisch berechnet):
- Aktuelle Last: 72.6 kW
- Erwartete Last (Median Vergleichstage): 8.0 (Median aus 7 Vergleichstagen) kW
- Differenz: +64.6 kW = +807.5 %
- Wetter: <Phase 3> °C, <Phase 3>
- Strompreis aktuell: <Phase 3> ct/kWh
- Geschätzte Mehrkosten dieser Anomalie: <Phase 3> EUR

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
```
</details>

| Variante | Ergebnis |
|---|---|
| V1_minimal | **hoch** · conf 0.92 · 6.1s<br>_Ursache:_ Unabsichtlicher Einschalten von Heizung oder Kühlanlagen während der Nacht.<br>_Empf.:_<br>1. Überprüfen Sie die Steuerung der HVAC-Systeme, um sicherzustellen, dass sie nicht unerwartet aktiviert werden.<br>2. Installieren Sie eine Überwachungssystem für den Stromverbrauch in der Nacht, um unerwartete Aktivitäten zu erkennen und zu dokumentieren.<br>3. Überprüfen Sie die Ladeinfrastruktur, da dies möglicherweise zu einem erhöhten Verbrauch führt. |
| V2_fewshot | **hoch** · conf 0.85 · 7.8s<br>_Ursache:_ Unnötige Betriebsstunden der Kühlanlagen im Gartencenter und der Getränkeauslage trotz geringer Nachtschwärme, möglicherweise auch unoptimale Regelung der HVAC-Systeme.<br>_Empf.:_<br>1. Überprüfen und optimieren der Temperaturregelung der Kühlanlagen im Gartencenter und bei den Getränken<br>2. Prüfen, ob die Betriebszeiten der Kühlanlagen auf die tatsächliche Nachtschwärme abgestimmt sind<br>3. Wartungstermin vereinbaren, um die Regelungssysteme der HVAC-Installationen zu überprüfen und anzupassen |
| V3_cot | **hoch** · conf 0.92 · 6.4s<br>_Ursache:_ Unabsichtlicher Betrieb der Kühlanlagen im Gartencenter während der Nachtzeit.<br>_Empf.:_<br>1. Überprüfen Sie die Programmierung und Schaltzeiten der Kühlanlagen, um unerwünschte Überlastungen zu vermeiden.<br>2. Prüfen Sie den Betriebsstatus aller Anlagen nach dem Feierabend, um eventuelle Unregelmäßigkeiten zu identifizieren.<br>3. Implementieren Sie eine tägliche Prüfung der Anlagenaufträge durch den Facility-Manager, um solche Fehler frühzeitig festzustellen. |

## nr 58 — Baumarkt_05 · autoencoder · vormittag

<details><summary>User-Prompt (Kontext)</summary>

```
Anomalie-Befund:
- Standort: Baumarkt_05
- Zeitpunkt: 06.06.2025 10:30, Freitag
- Feiertag: nein
- Detektion durch: autoencoder
- Segment: vormittag

Verbrauchs-Kontext (deterministisch berechnet):
- Aktuelle Last: 24.8 kW
- Erwartete Last (Median Vergleichstage): 0.0 (Median aus 7 Vergleichstagen) kW
- Differenz: +24.8 kW = n/a (Erwartung 0 kW, jede Last ist Abweichung) %
- Wetter: <Phase 3> °C, <Phase 3>
- Strompreis aktuell: <Phase 3> ct/kWh
- Geschätzte Mehrkosten dieser Anomalie: <Phase 3> EUR

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
```
</details>

| Variante | Ergebnis |
|---|---|
| V1_minimal | **hoch** · conf 0.92 · 5.9s<br>_Ursache:_ Eventuell Überlastung der Kühlanlagen im Gartencenter.<br>_Empf.:_<br>1. Überprüfen Sie die Betriebsstatus der Kühlgeräte und optimieren Sie die Temperatur-Regelung.<br>2. Prüfen Sie den Stromverbrauch der Beleuchtung in der Verkaufsfläche, um unnötige Überlastungen zu vermeiden.<br>3. Analysieren Sie die Anomalie weiter, um mögliche Fehlfunktionen oder Leistungsabfälle zu identifizieren. |
| V2_fewshot | **hoch** · conf 0.85 · 6.5s<br>_Ursache:_ Unvorhergesehene Anlieferung oder unerwarteter Kundenaufkommen am Freitagmorgen<br>_Empf.:_<br>1. Überprüfen, ob es eine Anlieferung gibt, die den Verbrauch erhöht hat<br>2. Kontrollieren, ob alle Bereiche der Verkaufsfläche optimiert beleuchtet werden (z.B. Durchgangslicht)<br>3. Wartungstermin vereinbaren, um Regelungen und Systeme zu überprüfen |
| V3_cot | **hoch** · conf 0.90 · 7.1s<br>_Ursache:_ Unvorhergesehene Anwendungsfall bei der Kühlung im Gartencenter, da normalerweise niedriges Verbrauchsprofil angetroffen wird.<br>_Empf.:_<br>1. Überprüfen Sie die Kühlanlagen im Gartencenter auf mögliche Fehlfunktionen oder Überlastungen.<br>2. Kontaktieren Sie den Lieferanten der Kühlgeräte, um eine schnelle Diagnose und eventuell Notbehandlung zu vereinbaren.<br>3. Bewerten Sie die Notwendigkeit einer temporären Reduzierung der Kühlleistung in Abhängigkeit von dem Wetter- und Verkaufsprofil. |

## nr 43 — Baumarkt_19 · cluster_segment · mittag

<details><summary>User-Prompt (Kontext)</summary>

```
Anomalie-Befund:
- Standort: Baumarkt_19
- Zeitpunkt: 09.02.2023 12:00, Donnerstag
- Feiertag: nein
- Detektion durch: cluster_segment
- Segment: mittag

Verbrauchs-Kontext (deterministisch berechnet):
- Aktuelle Last: 49.2 kW
- Erwartete Last (Median Vergleichstage): 55.8 (Median aus 5 Vergleichstagen) kW
- Differenz: -6.6 kW = -11.9 %
- Wetter: <Phase 3> °C, <Phase 3>
- Strompreis aktuell: <Phase 3> ct/kWh
- Geschätzte Mehrkosten dieser Anomalie: <Phase 3> EUR

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
```
</details>

| Variante | Ergebnis |
|---|---|
| V1_minimal | **mittel** · conf 0.85 · 5.8s<br>_Ursache:_ Eventuell ist ein Kühlschrank im Gartencenter defekt und verbraucht weniger Energie.<br>_Empf.:_<br>1. Überprüfen Sie den Kühlschrank im Gartencenter, ob er richtig funktioniert. Ersetzen Sie ihn, wenn nötig.<br>2. Prüfen Sie die Lichtinstallationen der Verkaufsfläche auf mögliche Leckage oder Defekte.<br>3. Verwalten Sie die Ladeinfrastruktur sorgfältiger und überwachen Sie deren Energieverbrauch. |
| V2_fewshot | **niedrig** · conf 0.75 · 7.2s<br>_Ursache:_ Kürzlich erhöhte Beleuchtungseffizienz oder optimierte HVAC-Regelung im Mittagsbereich, was die Last reduziert<br>_Empf.:_<br>1. Beleuchtungsstatus der Verkaufsfläche überprüfen und eventuell zusätzliche Einsparungen durch Anpassung der Leuchtdichte oder Tageslichtausnutzung prü<br>2. HVAC-Systeme überprüfen, ob eine optimierte Regelung die Last reduziert<br>3. Kundenfrequenz des Tages beobachten und gegebenenfalls Maßnahmen ergreifen |
| V3_cot | **mittel** · conf 0.85 · 6.0s<br>_Ursache:_ Möglicherweise ist ein Kühlregler defekt oder die Kühlanlagen laufen zu lange.<br>_Empf.:_<br>1. Überprüfen Sie den Kühlregler und stellen Sie sicher, dass er korrekt kalibriert ist.<br>2. Prüfen Sie die Kühlanlagen auf Lecks oder andere Defekte. Wenn nötig, lassen Sie sie ausfallen und reparieren.<br>3. Erhöhen Sie die Überwachung der Kühlanlagen und des Kühlreglers in den kommenden Tagen. |
