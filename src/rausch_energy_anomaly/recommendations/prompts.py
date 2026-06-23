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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rausch_energy_anomaly.recommendations.context import FullContext

# Spot-price thresholds (ct/kWh) that trigger a contextualising line in the
# user prompt. The average German day-ahead price 2023-2025 sat at roughly
# 6-15 ct/kWh, so a negative price is an over-supply signal and anything above
# 20 ct/kWh is atypically expensive.
PRICE_NEGATIVE_CT = 0.0
PRICE_HIGH_CT = 20.0

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

Verbrauchs-Kontext (deterministisch berechnet, nicht vom LLM zu schätzen):
- Aktuelle Last: {value_kw} kW
- Erwartete Last (Median Vergleichstage): {expected_kw} kW
- Differenz: {diff_kw} kW = {diff_pct} %
- Wetter zum Anomalie-Zeitpunkt (DWD-Station nahe Standort-PLZ {plz}): {wetter}
- Spotpreis (Stundenwert): {spotpreis}{preis_kontext}
- Geschätzte Mehrkosten dieser Anomalie: {mehrkosten}

Bitte gib eine strukturierte Empfehlung im vorgegebenen JSON-Format.
Sei konkret, nicht generisch. Beziehe dich auf den Baumarkt-Kontext.

Hinweise zu den Feldern:
- confidence: Dezimalzahl zwischen 0.0 und 1.0 (z.B. 0.85, nicht 85).
- vermutete_ursache: max. 250 Zeichen, konkret und standortbezogen statt allgemein.
- handlungsempfehlungen: genau 3 Stück, nach Priorität geordnet, je max. 150 Zeichen.
- Die Mehrkosten sind bereits berechnet; bei negativem Spotpreis können sie 0 oder
  negativ sein. Übernimm die Zahl, rechne sie nicht neu."""

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

_WEEKDAY_DE = {
    "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag",
    "Sunday": "Sonntag",
}


def _fmt_wetter(ctx: FullContext) -> str:
    if ctx.temperatur_c is None:
        return "Wetterdaten nicht verfügbar"
    parts = [f"{ctx.temperatur_c:.1f} °C", ctx.wetter_beschreibung or "k.A."]
    if ctx.niederschlag_mm is not None:
        parts.append(f"Niederschlag {ctx.niederschlag_mm:.1f} mm")
    if ctx.windgeschwindigkeit_kmh is not None:
        parts.append(f"Wind {ctx.windgeschwindigkeit_kmh:.0f} km/h")
    return ", ".join(parts)


def _fmt_spotpreis(ctx: FullContext) -> str:
    if ctx.spotpreis_ct_pro_kwh is None:
        return "Strompreis nicht verfügbar"
    s = f"{ctx.spotpreis_ct_pro_kwh:.2f} ct/kWh"
    if ctx.spotpreis_durchschnitt_24h_ct_pro_kwh is not None:
        s += f" (24h-Schnitt {ctx.spotpreis_durchschnitt_24h_ct_pro_kwh:.2f} ct/kWh)"
    return s


def _preis_kontext(spotpreis_ct: float | None) -> str:
    """One-line interpretation hint for extreme spot prices (empty if normal)."""
    if spotpreis_ct is None:
        return ""
    if spotpreis_ct < PRICE_NEGATIVE_CT:
        return ("Spotpreis ist negativ — Stromverbrauch wird in dieser Stunde "
                "belohnt, nicht bestraft.")
    if spotpreis_ct > PRICE_HIGH_CT:
        return "Spotpreis ist hoch — Mehrverbrauch besonders teuer."
    return ""


def _fmt_mehrkosten(ctx: FullContext) -> str:
    if ctx.mehrkosten_eur is None:
        return "nicht berechenbar (Preis fehlt)"
    return f"{ctx.mehrkosten_eur:.2f} EUR (über ~{ctx.dauer_h:g} h)"


def render_user_prompt(ctx: FullContext, feiertag: str = "nein") -> str:
    """Render USER_PROMPT_TEMPLATE from a FullContext, formatting missing fields.

    ``feiertag`` is not part of FullContext (it comes from annotation.csv); the
    caller passes it through, defaulting to "nein".
    """
    if ctx.expected_kw is None:
        expected_s, diff_s, pct_s = "n/a (keine Vergleichstage)", "n/a", "n/a"
    else:
        expected_s = f"{ctx.expected_kw:.1f} (Median aus {ctx.n_vergleichstage} Vergleichstagen)"
        diff_s = f"{ctx.diff_kw:+.1f}"
        pct_s = (
            f"{ctx.diff_pct:+.1f}" if ctx.diff_pct is not None
            else "n/a (Erwartung 0 kW, jede Last ist Abweichung)"
        )
    return USER_PROMPT_TEMPLATE.format(
        site=ctx.site,
        plz=ctx.plz or "unbekannt",
        timestamp_human=ctx.timestamp.strftime("%d.%m.%Y %H:%M"),
        wochentag=_WEEKDAY_DE.get(ctx.timestamp.strftime("%A"), ctx.timestamp.strftime("%A")),
        feiertag=feiertag,
        methode=ctx.method,
        segment=ctx.segment,
        value_kw=f"{ctx.value_kw:.1f}",
        expected_kw=expected_s,
        diff_kw=diff_s,
        diff_pct=pct_s,
        wetter=_fmt_wetter(ctx),
        spotpreis=_fmt_spotpreis(ctx),
        preis_kontext=(f"\n  → {pk}" if (pk := _preis_kontext(ctx.spotpreis_ct_pro_kwh)) else ""),
        mehrkosten=_fmt_mehrkosten(ctx),
    )
