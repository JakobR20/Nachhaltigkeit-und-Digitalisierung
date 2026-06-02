"""Cost-first anomaly browser (Apple-HIG) — main pages for the energy manager.

page_anomaly_list:   cost-prioritised card list with filters.
page_anomaly_detail: per-anomaly detail (load plot, transparent cost calc,
                     AI analysis, conditions).

Data source: the 66 annotated anomalies (reports/llm_recommendations/*.json),
because only those carry the full cost + cause analysis.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data_access import (
    load_cost_table,
    load_recommendation_detail,
    load_site_timeseries,
)
from app.styling import HIG_ACCENT, hig_pill, plotly_hig_layout

_MONTHS_DE = {1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
              7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November",
              12: "Dezember"}
_SEG_DE = {"nachts": "Nachts", "vormittag": "Vormittag", "mittag": "Mittag",
           "nachmittag": "Nachmittag"}


def _fmt_eur(v: float | None) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_dt(ts: str) -> tuple[str, str]:
    t = pd.Timestamp(ts)
    return f"{t.day}. {_MONTHS_DE[t.month]} {t.year}", t.strftime("%H:%M")


def _brand_header() -> None:
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown('<div class="hig-brand">THWS</div>'
                    '<div class="hig-brand-sub">Nachhaltigkeit &amp; Digitalisierung</div>',
                    unsafe_allow_html=True)
    with c2:
        if st.button("⚙", help="Forschungs-Ansicht"):
            st.session_state["_nav_to"] = "research"
            st.rerun()


# ---------------------------------------------------------------- list page
def page_anomaly_list() -> None:
    _brand_header()
    st.markdown('<div class="hig-title">Energie-Anomalien — '
                'Kostenpriorisierte Übersicht</div>', unsafe_allow_html=True)

    df = load_cost_table()
    f1, f2, f3, f4 = st.columns(4)
    site = f1.selectbox("Standort", ["Alle", *sorted(df["site"].unique())])
    zeitraum = f2.selectbox("Zeitraum", ["Gesamt", "Letzte 30 Tage", "Letzte 90 Tage"])
    mincost = f3.selectbox("Mindestkosten", ["Alle", "≥10 €", "≥50 €", "≥100 €"])
    sort = f4.selectbox("Sortierung",
                        ["Kosten hoch→niedrig", "Datum neu→alt", "Schweregrad"])

    view = df.copy()
    if site != "Alle":
        view = view[view["site"] == site]
    if zeitraum != "Gesamt":
        days = 30 if "30" in zeitraum else 90
        latest = pd.to_datetime(df["timestamp"], utc=True).max()
        cutoff = latest - pd.Timedelta(days=days)
        view = view[pd.to_datetime(view["timestamp"], utc=True) >= cutoff]
    if mincost != "Alle":
        thr = {"≥10 €": 10, "≥50 €": 50, "≥100 €": 100}[mincost]
        view = view[view["mehrkosten_eur"].fillna(0) >= thr]

    if sort == "Datum neu→alt":
        view = view.sort_values("timestamp", ascending=False)
    elif sort == "Schweregrad":
        order = {"hoch": 0, "mittel": 1, "niedrig": 2}
        view = view.sort_values(by="schweregrad", key=lambda s: s.map(order))
    else:
        view = view.sort_values("mehrkosten_eur", ascending=False, na_position="last")

    for r in view.itertuples():
        _list_card(r)

    total = view["mehrkosten_eur"].fillna(0).sum()
    st.markdown(
        f'<div class="hig-foot">{len(view)} Anomalien mit vollständiger Analyse · '
        f'{_fmt_eur(total)}<br><span style="font-size:12px">Weitere ~2.000 '
        f'statistische Detektionen ohne Detail-Analyse — siehe Forschungs-Ansicht ⚙'
        f'</span></div>', unsafe_allow_html=True)


def _list_card(r: Any) -> None:
    datum, uhrzeit = _fmt_dt(r.timestamp)
    seg = _SEG_DE.get(r.segment, r.segment)
    ursache = r.vermutete_ursache
    if len(ursache) > 80:
        ursache = ursache[:80].rsplit(" ", 1)[0] + "…"
    if r.diff_kw is not None and r.diff_kw >= 0:
        last_line = (f"+{r.diff_pct:.0f}% Last ({r.value_kw:.1f} kW statt "
                     f"{r.expected_kw:.1f} kW)") if r.diff_pct is not None else \
                    f"{r.value_kw:.1f} kW (Erwartung {r.expected_kw:.1f} kW)"
    else:
        last_line = f"Minderverbrauch {r.diff_kw:.1f} kW (Erwartung {r.expected_kw:.1f} kW)"

    st.markdown(
        f'<div class="hig-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span class="hig-cost">{_fmt_eur(r.mehrkosten_eur)}</span>'
        f'{hig_pill(r.schweregrad, r.schweregrad)}</div>'
        f'<div class="hig-site">{r.site}</div>'
        f'<div class="hig-meta">{seg}, {datum}, {uhrzeit} Uhr</div>'
        f'<div class="hig-meta">{last_line}</div>'
        f'<div class="hig-cause">{ursache}</div>'
        f'</div>', unsafe_allow_html=True)
    if st.button("Details ›", key=f"open_{r.nr}"):
        st.session_state["detail_nr"] = r.nr
        st.session_state["_nav_to"] = "detail"
        st.rerun()


# -------------------------------------------------------------- detail page
def page_anomaly_detail() -> None:
    nr = st.session_state.get("detail_nr")
    if nr is None:
        st.session_state["_nav_to"] = "list"
        st.rerun()
        return
    if st.button("‹ Zurück zur Übersicht"):
        st.session_state["_nav_to"] = "list"
        st.rerun()

    detail = load_recommendation_detail(nr)
    c, rec, ann = detail["context"], detail["recommendation"], detail["annotation"]
    datum, uhrzeit = _fmt_dt(c["timestamp"])
    seg = _SEG_DE.get(c["segment"], c["segment"])
    st.markdown(f'<div class="hig-brand" style="font-size:1.4rem">'
                f'{c["site"]} · {seg} · {datum}</div>', unsafe_allow_html=True)

    _block_plot(c)
    _block_cost(c)
    _block_ai(rec)
    _block_conditions(c, ann, rec)


def _block_plot(c: dict[str, Any]) -> None:
    site, ts = c["site"], pd.Timestamp(c["timestamp"])
    series = load_site_timeseries(site)
    win = series[(series.index >= ts - pd.Timedelta(days=3))
                 & (series.index <= ts + pd.Timedelta(days=3))]
    fig = go.Figure()
    fig.add_scatter(x=win.index, y=win.values, mode="lines", name="Last (kW)",
                    line=dict(color="#1C1C1E", width=1))
    if c["expected_kw"] is not None:
        fig.add_scatter(x=[win.index.min(), win.index.max()],
                        y=[c["expected_kw"], c["expected_kw"]], mode="lines",
                        name="Erwartung (Median Vergleichstage)",
                        line=dict(color="#8E8E93", width=1.4, dash="dash"))
    fig.add_scatter(x=[ts], y=[c["value_kw"]], mode="markers", name="Anomalie",
                    marker=dict(color="#FF3B30", size=13, symbol="x"))
    fig.update_layout(height=320, legend=dict(orientation="h", y=1.1),
                      **plotly_hig_layout())
    with st.container():
        st.markdown('<div class="hig-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)


def _block_cost(c: dict[str, Any]) -> None:
    diff = c["diff_kw"]
    dauer = c["dauer_h"]
    spot = c["spotpreis_ct_pro_kwh"]
    cost = c["mehrkosten_eur"]
    datum, uhrzeit = _fmt_dt(c["timestamp"])

    if diff is not None and diff < 0:
        body = (f"Minderverbrauch:  {abs(diff):.1f} kW unter Erwartung\n"
                "Hinweis: Unterverbrauch verursacht keine Mehrkosten.\n"
                "Möglicherweise Effizienzgewinn oder Anlagen-Ausfall — siehe KI-Analyse.")
    elif spot is not None and spot < 0:
        kwh = diff * dauer if diff is not None else 0
        body = (f"Mehrverbrauch:    {diff:.1f} kW über {dauer:g} Stunden = {kwh:.1f} kWh\n"
                f"× Spotpreis:      {spot:.2f} ct/kWh (negativ — Stromüberschuss)\n"
                "─────────────────────────────────────────────\n"
                "= Dieser Vorfall: 0,00 €\n\n"
                "Hinweis: Mehrverbrauch ist trotzdem auffällig, hatte aber zu diesem "
                "Zeitpunkt keinen Kostenimpact wegen negativer Spotpreise.")
    else:
        kwh = diff * dauer if diff is not None else 0
        jahr = (cost or 0) * 365
        body = (f"Mehrverbrauch:    {diff:.1f} kW über {dauer:g} Stunden = {kwh:.1f} kWh\n"
                f"× Spotpreis:      {spot:.2f} ct/kWh ({datum}, {uhrzeit} Uhr)\n"
                "─────────────────────────────────────────────\n"
                f"= Dieser Vorfall: {_fmt_eur(cost)}\n\n"
                "Falls jährlich vergleichbar:\n"
                f"≈ {_fmt_eur(jahr)} pro Jahr (365 × {_fmt_eur(cost)})")
    st.markdown('<div class="hig-card"><b>Kostenanalyse</b>'
                f'<div class="hig-calc">{body}</div></div>', unsafe_allow_html=True)


def _block_ai(rec: dict[str, Any]) -> None:
    actions = "".join(f"<li>{e}</li>" for e in rec["handlungsempfehlungen"])
    st.markdown(
        '<div class="hig-card">'
        '<div style="display:flex;justify-content:space-between;align-items:center">'
        '<b>KI-Analyse</b>'
        f'{hig_pill(rec["schweregrad"], rec["schweregrad"])}</div>'
        '<div style="font-size:15px;font-weight:500;margin-top:0.6rem">Vermutete Ursache</div>'
        f'<div style="font-size:15px">{rec["vermutete_ursache"]}</div>'
        '<div style="font-size:15px;font-weight:500;margin-top:0.8rem">'
        'Handlungsempfehlungen</div>'
        f'<ol style="font-size:15px;margin:0.3rem 0 0 1.1rem">{actions}</ol>'
        '</div>', unsafe_allow_html=True)


def _block_conditions(c: dict[str, Any], ann: dict[str, Any], rec: dict[str, Any]) -> None:
    feiertag = "Feiertag" if ann.get("feiertag") == "ja" else "kein Feiertag"
    rows = [
        f'Wetter: {c["temperatur_c"]} °C · {c["wetter_beschreibung"]}',
        f'Wochentag: {ann.get("wochentag")} · {feiertag}',
        f'Detektionsmethode: {c["method"]}',
        f'Konfidenz der KI-Analyse: {rec["confidence"]:.2f}',
    ]
    inner = "".join(f'<div class="hig-meta">{r}</div>' for r in rows)
    st.markdown(f'<div class="hig-card"><b>Rahmenbedingungen</b>{inner}</div>',
                unsafe_allow_html=True)


_ = HIG_ACCENT  # referenced via CSS; keep import meaningful
