"""RLM anomaly-detection dashboard (Streamlit + Plotly).

Demo artefact for Rausch Technology. Four pages:
  1. Übersicht        — site list, severity histogram, top-10, method card
  2. Methodenvergleich — kappa heatmap, X-sweep, inference table, comparison
  3. Standort-Detail   — load curve, method filters, hyperparameter sliders
  4. Anomalie-Detail   — per-anomaly plot, scores, LLM recommendation, context

Run: streamlit run app/dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# `streamlit run app/dashboard.py` puts app/ on sys.path, not the repo root, so the
# `app.` package imports below would fail. Add the repo root explicitly.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from app.data_access import (  # noqa: E402
    METHODS,
    annotated_index,
    expected_profile,
    load_comparison_markdown,
    load_config,
    load_flag_matrix,
    load_recommendation_detail,
    load_recommendations,
    load_scores_for_site,
    load_site_timeseries,
    sites,
)
from app.method_meta import comparison_table, inference_times, kappa_matrix  # noqa: E402
from app.styling import header, inject_css, severity_badge  # noqa: E402

sites_list = sites

st.set_page_config(page_title="RLM-Anomalieerkennung", layout="wide")


def page_overview() -> None:
    cfg = load_config()
    matrix = load_flag_matrix()
    recs = load_recommendations()
    special = cfg.get("special_sites", {})
    colors = cfg["method_colors"]
    sev_colors = cfg["severity_colors"]

    n_sites = len(matrix)
    n_special = len(special)
    header("Übersicht",
           f"{n_sites} Standorte ({n_special} mit eingeschränktem Datenstand) · "
           f"4 Methoden · {len(recs)} annotierte Anomalien")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown("**Geflaggte Anomalien je Standort und Methode**")
        display = matrix.copy()
        display["Standort"] = display["site"].apply(
            lambda s: f"⚠️ {s}" if s in special else s)
        cols = ["Standort", *colors.keys(), "gesamt"]
        st.dataframe(
            display[cols].sort_values("gesamt", ascending=False),
            width="stretch", hide_index=True,
        )
        if special:
            for s, reason in special.items():
                st.caption(f"⚠️ {s}: {reason}")

    with col_r:
        st.markdown("**Schweregrad-Verteilung (alle Empfehlungen)**")
        sev_order = ["hoch", "mittel", "niedrig"]
        counts = recs["schweregrad"].value_counts().reindex(sev_order).fillna(0)
        fig = px.bar(
            x=sev_order, y=counts.values,
            color=sev_order, color_discrete_map=sev_colors,
            labels={"x": "Schweregrad", "y": "Anzahl"},
        )
        fig.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")

    st.divider()
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**Top-10-Anomalien (höchste Modell-Konfidenz)**")
        top = recs.sort_values("confidence", ascending=False).head(
            cfg["pages"]["overview_top_n"])
        st.dataframe(
            top[["nr", "site", "timestamp", "method", "schweregrad",
                 "confidence", "vermutete_ursache"]],
            width="stretch", hide_index=True,
        )
        st.caption("Detailansicht je Anomalie: Seite »Anomalie-Detail«.")

    with col2:
        st.markdown("**Methoden auf einen Blick (κ-Komplementarität)**")
        _method_card()


def _method_card() -> None:
    km = kappa_matrix()
    if not km:
        st.info("Methodenvergleich-Tabelle nicht gefunden.")
        return
    pairs = [(a, b) for i, a in enumerate(METHODS) for b in METHODS[i + 1:]]
    rows = [{"Paar": f"{a} ↔ {b}", "κ": km.get((a, b))} for a, b in pairs]
    st.dataframe(rows, width="stretch", hide_index=True)
    st.caption("Niedriges κ = komplementäre Methoden (finden verschiedene Anomalien). "
               "Volle Heatmap: Seite »Methodenvergleich«.")


def page_method_comparison() -> None:
    colors = load_config()["method_colors"]
    header("Methodenvergleich",
           "Wie sich die vier Erkennungsmethoden ergänzen, wie viel sie finden "
           "und was sie kosten.")

    # Karte 1 — Komplementarität
    st.markdown("#### 1 · Komplementarität — finden die Methoden dasselbe?")
    c1a, c1b = st.columns([3, 2])
    with c1a:
        km = kappa_matrix()
        z = [[km.get((a, b)) for b in METHODS] for a in METHODS]
        fig = go.Figure(data=go.Heatmap(
            z=z, x=list(METHODS), y=list(METHODS),
            colorscale="Blues", zmin=0, zmax=1,
            text=[[f"{v:.2f}" if v is not None else "" for v in row] for row in z],
            texttemplate="%{text}", colorbar=dict(title="κ"),
        ))
        fig.update_layout(height=360, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    with c1b:
        st.markdown(
            "Die vier Methoden finden **unterschiedliche** Anomalien. Niedrige "
            "κ-Werte (−0,01 bis 0,11) bedeuten: kaum Überlappung — **komplementäre "
            "Sichten**. Ein Ensemble deckt mehr ab als jede Methode allein.")

    st.divider()

    # Karte 2 — Methoden-Statistik (erkannte Anomalien je Methode)
    st.markdown("#### 2 · Wie viel findet jede Methode?")
    c2a, c2b = st.columns([3, 2])
    with c2a:
        matrix = load_flag_matrix()
        totals = {m: int(matrix[m].sum()) for m in METHODS}
        fig2 = go.Figure(go.Bar(
            x=list(METHODS), y=[totals[m] for m in METHODS],
            marker_color=[colors[m] for m in METHODS],
            text=[f"{totals[m]:,}" for m in METHODS], textposition="outside",
        ))
        fig2.update_layout(height=360, margin=dict(t=10, b=10),
                           yaxis_title="Geflaggte Anomalien (alle Standorte)")
        st.plotly_chart(fig2, width="stretch")
    with c2b:
        st.markdown(
            "Bei Standard-Schwelle erkennt jede Methode zwischen **1–5 %** der "
            "Datenpunkte. **ARIMA / Z-Score:** Punkt-Anomalien (einzelne "
            "15-min-Werte). **Cluster:** auffällige Tagessegmente. **Autoencoder:** "
            "untypische Tagesform.")

    st.divider()

    # Karte 3 — Inferenzkosten
    st.markdown("#### 3 · Was kostet jede Methode?")
    c3a, c3b = st.columns([3, 2])
    with c3a:
        it = inference_times()
        methods = [m for m in METHODS if m in it]
        fig3 = go.Figure()
        fig3.add_bar(name="fit (s)", x=methods, y=[it[m]["fit_s"] for m in methods],
                     marker_color="#1f77b4")
        fig3.add_bar(name="score (s)", x=methods, y=[it[m]["score_s"] for m in methods],
                     marker_color="#ff7f0e")
        fig3.update_layout(barmode="group", height=360, margin=dict(t=10, b=10),
                           yaxis_title="Sekunden", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig3, width="stretch")
    with c3b:
        st.markdown(
            "**ARIMA** dominiert die Kosten (~2 Min/Standort). **Z-Score** und "
            "**Cluster** sind quasi gratis. **Autoencoder:** ~5 s/Standort nach "
            "dem Training.")

    with st.expander("Methodische Details (Vergleichstabelle Schritt 11)"):
        rows = comparison_table()
        if rows:
            st.dataframe(rows, width="stretch", hide_index=True)
        else:
            st.markdown(load_comparison_markdown())


def _threshold_flags(
    scores: pd.DataFrame, method: str, thresholds: dict[str, float]
) -> pd.DataFrame:
    """Re-threshold precomputed scores for one method (no re-inference)."""
    sub = scores[scores["method"] == method]
    if method == "zscore_stl":
        return sub[sub["score"].abs() > thresholds["zscore"]]
    if method == "arima":
        # ARIMA keeps its precomputed flags (re-inference is ~10 min); sigma slider
        # re-thresholds the standardised residual score instead.
        return sub[sub["score"].abs() > thresholds["arima_sigma"]]
    if method == "autoencoder":
        # AE score is a reconstruction error; the percentile slider maps to a
        # score quantile over this site's AE scores.
        if sub.empty:
            return sub
        cut = sub["score"].quantile(thresholds["ae_pct"] / 100.0)
        return sub[sub["score"] > cut]
    return sub[sub["flag"] == True]  # noqa: E712 - cluster_segment keeps native flags


def page_site_detail() -> None:
    cfg = load_config()
    colors = cfg["method_colors"]
    special = cfg.get("special_sites", {})

    header("Standort-Detail",
           "Lastgang mit Erwartung, Methoden-Aktivität und die stärksten Anomalien.")
    site = st.selectbox("Standort", sites_list())
    if site in special:
        st.warning(f"⚠️ {site}: {special[site]}")

    series = load_site_timeseries(site)
    scores = load_scores_for_site(site)

    tmin, tmax = series.index.min().date(), series.index.max().date()
    c1, c2 = st.columns(2)
    start = c1.date_input("Von", value=tmin, min_value=tmin, max_value=tmax)
    end = c2.date_input("Bis", value=min(tmin + pd.Timedelta(days=30), tmax),
                        min_value=tmin, max_value=tmax)
    mask = (series.index.date >= start) & (series.index.date <= end)
    window = series[mask]
    if window.empty:
        st.info("Kein Lastgang im gewählten Zeitraum.")
        return

    st.sidebar.markdown("### Hyperparameter (Re-Thresholding)")
    thresholds = {
        "zscore": st.sidebar.slider("Z-Score-Schwelle", 1.0, 6.0, 3.0, 0.1),
        "arima_sigma": st.sidebar.slider("ARIMA-Sigma", 1.0, 6.0, 3.0, 0.1),
        "ae_pct": st.sidebar.slider("AE-Threshold-Perzentil", 90.0, 99.9, 99.0, 0.1),
    }
    st.sidebar.caption("Verschiebt die Flag-Schwelle auf vorberechneten Scores "
                       "(keine Live-Inferenz; ARIMA-Kosten ~10 min).")

    # 1. Hauptplot: Last + Erwartung (keine X-Marker)
    profile = expected_profile(site)
    exp_win = pd.Series([profile.get((t.dayofweek, t.time())) for t in window.index],
                        index=window.index)
    fig = go.Figure()
    fig.add_scatter(x=window.index, y=window.values, mode="lines",
                    name="Last (kW)", line=dict(color="#444", width=1))
    fig.add_scatter(x=exp_win.index, y=exp_win.values, mode="lines",
                    name="Erwartung (Median Vergleichstage)",
                    line=dict(color="#2ca02c", width=1.2, dash="dash"))
    fig.update_layout(height=360, margin=dict(t=10, b=10), yaxis_title="kW",
                      legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, width="stretch")

    # 2. Methoden-Streifen: wann hat welche Methode geflaggt
    wmin, wmax = window.index.min(), window.index.max()
    flagged_by_method = {
        m: _threshold_flags(scores, m, thresholds).pipe(
            lambda d: d[(d["timestamp"] >= wmin) & (d["timestamp"] <= wmax)])
        for m in METHODS
    }
    strip = go.Figure()
    for i, m in enumerate(METHODS):
        fl = flagged_by_method[m]
        strip.add_scatter(
            x=fl["timestamp"], y=[i] * len(fl), mode="markers",
            name=f"{m} ({len(fl)})",
            marker=dict(color=colors[m], size=6, symbol="line-ns-open", line=dict(width=1.5)),
        )
    strip.update_layout(
        height=150, margin=dict(t=10, b=10),
        yaxis=dict(tickmode="array", tickvals=list(range(len(METHODS))),
                   ticktext=list(METHODS), range=[-0.5, len(METHODS) - 0.5]),
        xaxis=dict(range=[wmin, wmax]), showlegend=False,
    )
    st.markdown("**Methoden-Aktivität** (vertikale Striche = geflaggte Zeitpunkte)")
    st.plotly_chart(strip, width="stretch")

    # 3. Top-5-Anomalien des Fensters (nach |score|)
    _render_top5(site, flagged_by_method, series, profile, colors)
    st.caption("Top 5 nach Anomalie-Stärke im gewählten Zeitraum. Karten mit "
               "Details-Link wurden manuell plausibilitätsgeprüft und liegen als "
               "LLM-Empfehlung vor.")


def _render_top5(
    site: str,
    flagged_by_method: dict[str, pd.DataFrame],
    series: pd.Series,
    profile: pd.Series,
    colors: dict[str, str],
) -> None:
    pool = []
    for m, fl in flagged_by_method.items():
        for r in fl.itertuples():
            pool.append((abs(r.score), r.timestamp, m, r.score))
    pool.sort(reverse=True)
    top = pool[:5]
    if not top:
        st.info("Keine geflaggten Anomalien im gewählten Zeitraum.")
        return

    annotated = annotated_index()
    cols = st.columns(len(top))
    for col, (_, ts, method, score) in zip(cols, top, strict=False):
        value = series.get(ts)
        expected = profile.get((ts.dayofweek, ts.time()))
        diff = value - expected if (value is not None and expected is not None) else None
        pct = (100 * diff / expected) if (diff is not None and expected) else None
        nr = annotated.get((site, str(ts)))
        with col:
            badge = "✓ annotiert" if nr else "—"
            border = "#2ca02c" if nr else "#d1d5db"
            diff_txt = (f"{diff:+.1f} kW ({pct:+.0f} %)" if diff is not None
                        else f"score {score:+.1f}")
            st.markdown(
                f'<div style="border:1px solid {border};border-left:4px solid '
                f'{colors[method]};border-radius:8px;padding:0.6rem;font-size:0.85rem">'
                f'<b>{pd.Timestamp(ts).strftime("%d.%m.%Y %H:%M")}</b><br>'
                f'<span style="color:{colors[method]}">{method}</span><br>'
                f'{diff_txt}<br><span style="color:#6b7280">{badge}</span></div>',
                unsafe_allow_html=True)
            if nr and st.button("Details", key=f"to_{nr}", width="stretch"):
                st.session_state["goto_nr"] = nr
                st.session_state["_nav_to"] = "Anomalie-Detail"
                st.rerun()


def page_anomaly_detail() -> None:
    cfg = load_config()
    colors = cfg["method_colors"]
    recs = load_recommendations()

    header("Anomalie-Detail", "Lastgang, Score, LLM-Empfehlung und Kontext je Anomalie.")
    labels = [f"nr {r.nr} · {r.site} · {r.method} · {r.timestamp}"
              for r in recs.itertuples()]
    # honour a deep-link from the site-detail top-5 cards
    default = 0
    goto = st.session_state.pop("goto_nr", None)
    if goto is not None:
        matches = recs.index[recs["nr"] == goto].tolist()
        if matches:
            default = recs.index.get_loc(matches[0])
    idx = st.selectbox("Anomalie", range(len(labels)), index=default,
                       format_func=lambda i: labels[i])
    row = recs.iloc[idx]
    nr = row["nr"]
    detail = load_recommendation_detail(nr)
    ctx, rec, ann = detail["context"], detail["recommendation"], detail["annotation"]

    # Lastgang ±3 Tage
    series = load_site_timeseries(row["site"])
    ts = pd.Timestamp(row["timestamp"])
    lo, hi = ts - pd.Timedelta(days=3), ts + pd.Timedelta(days=3)
    win = series[(series.index >= lo) & (series.index <= hi)]
    value_kw = ctx.get("value_kw")
    expected_kw = ctx.get("expected_kw")
    diff_kw = ctx.get("diff_kw")
    diff_pct = ctx.get("diff_pct")

    fig = go.Figure()
    fig.add_scatter(x=win.index, y=win.values, mode="lines", name="Last (kW)",
                    line=dict(color="#888", width=1))
    if expected_kw is not None:
        # horizontal expected-value band: a typical comparison day at this time
        fig.add_scatter(x=[win.index.min(), win.index.max()],
                        y=[expected_kw, expected_kw], mode="lines",
                        name="Erwartung (Median Vergleichstage)",
                        line=dict(color="#2ca02c", width=1.5, dash="dash"))
    fig.add_scatter(x=[ts], y=[value_kw], mode="markers", name="Anomalie",
                    marker=dict(color=colors.get(row["method"], "#d62728"),
                                size=14, symbol="x"))
    # direction annotation at the marker (Über-/Unterlast + magnitude)
    if diff_kw is not None:
        richtung = "Überlast" if diff_kw > 0 else "Unterlast"
        pct_txt = f" ({diff_pct:+.0f} %)" if diff_pct is not None else ""
        fig.add_annotation(x=ts, y=value_kw, text=f"{richtung}: {diff_kw:+.1f} kW{pct_txt}",
                           showarrow=True, arrowhead=2, ax=0, ay=-40,
                           font=dict(size=11, color="#333"),
                           bgcolor="rgba(255,255,255,0.8)")
    fig.update_layout(height=360, margin=dict(t=10, b=10), yaxis_title="kW",
                      legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)

    with left:
        sev = rec["schweregrad"]
        actions = "".join(f"<li>{e}</li>" for e in rec["handlungsempfehlungen"])
        st.markdown(
            f'<div class="dash-card llm">'
            f'<h4>LLM-Empfehlung &nbsp; {severity_badge(sev)} '
            f'<span style="color:#6b7280;font-size:0.85rem">· Konfidenz '
            f'{rec["confidence"]:.2f}</span></h4>'
            f'<b>Vermutete Ursache:</b> {rec["vermutete_ursache"]}'
            f'<ol style="margin:0.5rem 0 0 1.1rem;padding:0">{actions}</ol>'
            f'</div>',
            unsafe_allow_html=True)
        st.caption(f"Modell: {detail.get('llm_model')} · "
                   f"{detail.get('processing_time_s')} s · Versuche: {detail.get('attempts')}")

    with right:
        st.markdown('<div class="dash-card context"><h4>Kontext (deterministisch '
                    'berechnet)</h4></div>', unsafe_allow_html=True)
        st.table({
            "Feld": ["Aktuelle Last", "Erwartete Last", "Differenz",
                     "Wetter", "Spotpreis", "Geschätzte Mehrkosten"],
            "Wert": [
                f"{ctx.get('value_kw')} kW",
                f"{ctx.get('expected_kw')} kW",
                f"{ctx.get('diff_kw')} kW ({ctx.get('diff_pct')} %)",
                f"{ctx.get('temperatur_c')} °C, {ctx.get('wetter_beschreibung')}",
                f"{ctx.get('spotpreis_ct_pro_kwh')} ct/kWh",
                f"{ctx.get('mehrkosten_eur')} EUR (~{ctx.get('dauer_h')} h)",
            ],
        })

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Score & Komplementarität (κ zu anderen Methoden)**")
        km = kappa_matrix()
        method = row["method"]
        st.markdown(f"Methode **{method}** · Score `{float(ann['score']):.2f}` · "
                    f"Rang {ann['rang_in_methode']} · Segment {ann['segment']}")
        krows = [{"vs. Methode": m, "κ": km.get((method, m))}
                 for m in METHODS if m != method]
        st.dataframe(krows, width="stretch", hide_index=True)
    with c2:
        st.markdown("**Annotation**")
        plaus = ann.get("label") or "—"
        st.markdown(f"Plausibilitäts-Label: **{plaus}**")
        if ann.get("also_flagged_by"):
            st.markdown(f"Auch geflaggt von: {ann['also_flagged_by']}")
        st.markdown(f"Feiertag: {ann.get('feiertag')} · Wochentag: {ann.get('wochentag')}")

    csv_line = row.to_frame().T.to_csv(index=False)
    st.download_button("CSV-Zeile exportieren", csv_line,
                       file_name=f"anomalie_{nr}.csv", mime="text/csv")


PAGES = {
    "Übersicht": page_overview,
    "Methodenvergleich": page_method_comparison,
    "Standort-Detail": page_site_detail,
    "Anomalie-Detail": page_anomaly_detail,
}


def main() -> None:
    inject_css()
    cfg = load_config()
    b = cfg["branding"]
    st.sidebar.markdown(f"### {b['logo_placeholder']}")
    st.sidebar.title(b["title"])
    st.sidebar.caption(b["subtitle"])
    # a deep-link from the site-detail cards sets _nav_to before the radio renders
    if "page" not in st.session_state:
        st.session_state["page"] = "Übersicht"
    nav_to = st.session_state.pop("_nav_to", None)
    if nav_to is not None:
        st.session_state["page"] = nav_to
    choice = st.sidebar.radio("Seite", list(PAGES.keys()), key="page")
    PAGES[choice]()


if __name__ == "__main__":
    main()
