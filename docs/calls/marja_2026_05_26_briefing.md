# Briefing — Call mit Marja Wahl (RAUSCH), Di 26.05.2026

> Projekt: KI-gestützte Anomalieerkennung im Energieverbrauch (DatenWerKIOS, Cluster 2 / Aufgabe 3).
> Bearbeitende: Jakob & Felix · THWS, M. Digital Business Systems.
> Zweck dieses Dokuments: kompakter Stand für den Call. Methodische Tiefe in
> `docs/konzept/methodenwahl_defense.md` und `docs/konzept/konzept.md`.

## 1. Executive Summary

Wir entwickeln eine **erklärbare** Pipeline zur Anomalieerkennung auf Smart-Meter-Lastgängen. Forschungsfrage: *Wie lässt sich eine erklärbare Anomalieerkennung bauen, die (a) ohne pro-Standort-Training auf neue Liegenschaften übertragbar ist und (b) automatisierte Handlungsempfehlungen generiert?*

**Stand:** EDA, Feature-Engineering und eine Z-Score-Baseline sind fertig und reproduzierbar (Notebooks `01`–`03`). Die ARIMA-Hauptmethode ist der nächste Schritt.

**Wichtigster Befund bisher:** Die Baseline flaggt fast ausschließlich **Feiertage/Schließtage** als „Anomalien" — ein erklärbarer Fehler der reinen Saisonzerlegung. Das motiviert direkt die gewählte Hauptmethode (SARIMAX mit Feiertags-Regressor). Wir bringen also nicht nur Zahlen, sondern eine datenbegründete Methodenwahl mit.

**Für den Call brauchen wir von dir v. a.:** Standorte der Baumärkte, etwaige Anomalie-Labels, Einordnung Lastgang-vs-ZRV-Daten und Beispiele typischer Anomalien aus eurer Praxis (Details §6).

## 2. Datenbasis & EDA-Befunde

- **Umfang:** 77 Excel-Dateien in 5 Branchen (Baumärkte, Ladestationen, Tankstellen, Handel, Büro), 15-Minuten-Auflösung, Zeitraum ~2023-01-01 bis 2026-03-13.
- **Hauptscope:** **Baumärkte** (26 Zähler). Nach Ausschluss von **3 flachen Zählern** (`Baumarkt_01/_02/_04`, vmax < 1 kW — vermutlich Einheiten-Bug W statt kW oder Unterzähler) verbleiben **23 solide Zähler**. Validierung: `Handel/Lastgang_34` (kWh + Status-Flag).
- **Drei Quellformate** vereinheitlicht (Lastgang kWh, ZRV kW, ZRV mit Metadaten-Kopf) → einheitliches Schema (kW, MultiIndex meter_id × timestamp, Europe/Berlin); Loader mit stabiler meter_id-Zuordnung.
- **Saisonalität:** dominant **täglich + wöchentlich** (ACF-Peaks bei lag 24/168); **k = 3** Tagesprofil-Cluster (über Silhouette bestimmt).
- **Externe Daten integriert:** DWD-Wetter (Würzburg als Proxy bis Standortklärung) und EPEX-Day-Ahead-Preise (DE-LU), beide gecacht und auf Stundenebene gejoint.
- **Wetter ↔ Verbrauch (auflösungsabhängig — methodisch zentral):**

  | Auflösung | Korrelation Temp↔Verbrauch | Lesart |
  |-----------|----------------------------|--------|
  | stündlich, roh | r ≈ 0,11 | Tageszyklus überdeckt das Signal (Artefakt) |
  | Tagesmittel | median r ≈ −0,32 (22/23 negativ) | klares Heizsignal |
  | STL-Residuum | median r ≈ 0,02 | Wetter durch STL bereits absorbiert |

  → Konsequenz: der Anomalie-Score (STL-Residuum) ist **wetterrobust**.

## 3. Methodische Architektur (mit Kurzbegründung)

Datenfluss: Smart-Meter → Loader (Normalisierung, tz, stabile IDs) → Feature-Engineering (+ Wetter/Preis/Kalender) → Detection → Score → LLM-Empfehlung → Dashboard.

| Baustein | Wahl | Kurzbegründung (Details: `methodenwahl_defense.md`) |
|----------|------|------------------------------------------------------|
| Saisonbereinigung | **STL** (period=168, robust) | Trend + robuste Saison, zitierbar; Residuum empirisch wetterunabhängig (#3) |
| Baseline | **globaler Z-Score** auf STL-Residuum | einfacher, voll erklärbarer Vergleichsmaßstab (#7, #8) |
| Cluster | **k-Means** auf normierten Tagesprofilen, k=3 | interpretierbare Centroide für Modell-Zuordnung (#4, #5) |
| **Hauptmethode** | **SARIMAX pro Cluster**, Residuum/Prädiktionsintervall als Score | modelliert Zeitstruktur explizit, Konfidenzband ist erklärbar (#9) |
| Kalender | **`is_holiday`-Exogen** in SARIMAX | direkt durch Baseline-Befund motiviert (#10) |
| Empfehlungen | **lokales LLM (Llama 3.2 3B) via Ollama**, JSON-Schema | DSGVO-konform lokal; Format erzwungen, 3B genügt (#13, #14) |
| Übertragbarkeit | **cluster-basiert** (Centroid-Zuordnung, kein pro-Zähler-Training) | adressiert Forschungsfrage (a) (#15) |

**Bewusst nur diskutiert, nicht implementiert:** LSTM und Foundation Models (Chronos/TranAD/TimeRCD) — Begründung: Erklärbarkeit als nicht-funktionales Pflichtmerkmal in kritischer Energieinfrastruktur (#11, #12).

**Warum SARIMAX statt Isolation Forest (Kernargument):** Isolation Forest ignoriert die zeitliche Struktur (statische Dichteschätzung), SARIMAX modelliert die Erwartung *für jeden Zeitpunkt* → das Residuum ist die echte Kontext-Anomalie, und das Konfidenzband ist im Dashboard unmittelbar nachvollziehbar.

## 4. Baseline-Ergebnisse (Z-Score auf STL-Residuum)

- **14.712 Anomalien** bei |z| > 3 über 23 Zähler; Rate **1,7–3,2 %** pro Zähler (sehr gleichmäßig → systematischer Methoden-Effekt, kein einzelner Defekt-Zähler).
- **2,84 % beobachtet vs. 0,27 % theoretisch** → **fat-tailed** Residuen; die Schwelle ist empirisch zu kalibrieren.
- **Alle Top-10-Anomalien sind Feiertage** (negative Residuen / Schließtage: Weihnachten, Ostermontag, Tag der Deutschen Einheit, Heilige Drei Könige) — **keine Defekte**, sondern Schließungen.
- **Wochenenden werden problemlos absorbiert** (STL lernt die Wochenstruktur) — Fehlalarme entstehen nur an *irregulären* Feiertagen.

**Vier Limitationen (motivieren die Hauptmethode):** L1 fat tails → Schwelle empirisch; L2 keine Feiertags-Awareness → **SARIMAX mit `is_holiday`**; L3 Heteroskedastizität → kontextabhängiges Prädiktionsintervall; L4 kein zeitlicher Kontext → forecasting-basierte Bewertung.

## 5. Nächste Schritte

- **SARIMAX mit `is_holiday`** pro Cluster (Woche 3) — Zielnachweis: Verschwinden der Feiertags-Fehlalarme bei besserem Treffer auf echte Events.
- **Übertragbarkeitstest** auf einer ungesehenen Branche (ergebnisoffen).
- **LLM-Empfehlungskomponente** (Ollama, strukturierter Output).
- **Dashboard-Wireframe** + Paper/Poster.

## 6. Offene Punkte für Marja (Call-Ziel)

1. **Standorte der Baumärkte** — für korrekte Wetterstationen und das richtige Feiertags-Bundesland (unsere Top-10 enthalten „Heilige Drei Könige" → deutet auf Süddeutschland/Bayern; bitte bestätigen).
2. **Labels für bekannte Anomalien** — gibt es dokumentierte Störfälle/Events? Schon wenige würden eine echte Evaluation (statt „ground-truth-lite") ermöglichen.
3. **Vergleichbarkeit Lastgang (kWh + Status-Flag) vs. ZRV (kW)** — sind das dieselben Messpunkte in anderem Export? Und: sind die flachen Zähler (vmax < 1 kW) ein Einheiten-Thema (W statt kW) oder Unterzähler?
4. **Typische Anomalien aus eurer Praxis** — welche Muster seht ihr real (Dauerlast nachts, Lastabwürfe, defekte Kälte-/Lüftungstechnik, Stand-by-Verbräuche)? Das schärft, worauf die Methode optimieren soll.
