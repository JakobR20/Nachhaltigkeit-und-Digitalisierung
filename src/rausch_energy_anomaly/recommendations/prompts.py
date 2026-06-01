"""Prompt constants for qwen2.5:7b anomaly recommendations.

Step B defines the *base* prompts (Variant 1, minimal). Step C composes the
three test variants from these constants so the experiment is reproducible:

- Variant 1 (minimal):       SYSTEM_PROMPT_BASE
- Variant 2 (few-shot):      SYSTEM_PROMPT_BASE + "\\n\\n" + FEWSHOT_EXAMPLES
- Variant 3 (chain-of-thought): SYSTEM_PROMPT_BASE + "\\n\\n" + COT_HINT

All variants share USER_PROMPT_TEMPLATE.

Production prompt = V2 (few-shot), chosen after qualitative comparison of
V1/V2/V3 on 5 test anomalies. See reports/llm_evaluation/variant_comparison.md.
The three variant compositions are kept as constants for reproducibility; the
pipeline imports SYSTEM_PROMPT_PRODUCTION.
"""

from __future__ import annotations

SYSTEM_PROMPT_BASE = """\
Du bist ein Energie-Anomalie-Experte für gewerbliche Baumärkte. Du bewertest \
erkannte Anomalien in RLM-Lastgängen (Leistung in kW, 15-Minuten-Auflösung) und \
gibst dem Facility-Management konkrete, umsetzbare Handlungsempfehlungen.

Du kennst die typischen Großverbraucher eines Baumarkts: Heizung/Lüftung/Klima \
(HVAC), Beleuchtung der Verkaufsfläche, Kühlung im Gartencenter und bei Getränken, \
Drucklufterzeugung, Pumpen sowie Ladeinfrastruktur. Normalbetrieb richtet sich nach \
den Öffnungszeiten (i.d.R. Mo–Sa, sonntags geschlossen); nachts und sonntags ist \
nur eine niedrige Grundlast zu erwarten.

Antworte ausschließlich im vorgegebenen JSON-Format, ohne Text davor oder danach."""

USER_PROMPT_TEMPLATE = """\
Anomalie-Befund:
- Standort: {site}
- Zeitpunkt: {timestamp_human}, {wochentag}
- Feiertag: {feiertag}
- Detektion durch: {methode}
- Segment: {segment}

Verbrauchs-Kontext (deterministisch berechnet):
- Aktuelle Last: {value_kw} kW
- Erwartete Last (Median Vergleichstage): {expected_kw} kW
- Differenz: {diff_kw} kW = {diff_pct} %
- Wetter: {temp} °C, {weather_desc}
- Strompreis aktuell: {price_ct} ct/kWh
- Geschätzte Mehrkosten dieser Anomalie: {extra_cost_eur} EUR

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen."""

# Two hand-authored input -> output pairs grounded in Baumarkt context (Variant 2).
FEWSHOT_EXAMPLES = """\
Zur Orientierung zwei Beispiele für gute Empfehlungen:

Beispiel 1 — Befund: Baumarkt, Sonntag 03:00 (geschlossen), aktuelle Last 44 kW, \
erwartet 8 kW (+450 %), 3 °C.
{"schweregrad": "hoch", "vermutete_ursache": "Heizung/Lüftung läuft auch sonntags \
durchgehend, keine Nachtabsenkung trotz geschlossener Filiale", \
"handlungsempfehlungen": ["Zeitprogramm der HVAC-Steuerung auf Öffnungszeiten \
einstellen", "Nacht- und Wochenend-Absenkung aktivieren", "Wartungstermin zur \
Prüfung der Regelung vereinbaren"], "confidence": 0.82}

Beispiel 2 — Befund: Baumarkt, Dienstag 14:00 (geöffnet), aktuelle Last 71 kW, \
erwartet 95 kW (-25 %), 22 °C.
{"schweregrad": "niedrig", "vermutete_ursache": "Geringere Last als erwartet, \
vermutlich schwächeres Kundenaufkommen oder ausgeschaltete Teilbeleuchtung, kein \
Defekt erkennbar", "handlungsempfehlungen": ["Kundenfrequenz des Tages gegenprüfen", \
"Beleuchtungs- und Lüftungsstatus der Verkaufsfläche kontrollieren", "Kein \
Soforthandlungsbedarf, im Monitoring beobachten"], "confidence": 0.6}"""

COT_HINT = """\
Überlege zuerst still, welche typischen Baumarkt-Verbraucher (HVAC, Beleuchtung, \
Kühlung, Druckluft, Pumpen, Ladeinfrastruktur) zu diesem Anomalie-Typ passen — \
Richtung der Abweichung, Tageszeit/Segment, Öffnungsstatus und Außentemperatur. \
Gib anschließend NUR das JSON aus, ohne deine Überlegung sichtbar zu machen."""

# Frozen production prompt (Step D): V2 few-shot won the qualitative comparison.
# The pipeline imports this constant; the variant constants above stay for repro.
SYSTEM_PROMPT_PRODUCTION = SYSTEM_PROMPT_BASE + "\n\n" + FEWSHOT_EXAMPLES
