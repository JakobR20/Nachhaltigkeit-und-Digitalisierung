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
    COMPARISON_MD,
    METHODS,
    load_comparison_markdown,
    load_config,
    load_flag_matrix,
    load_recommendations,
    load_scores_for_site,
    load_site_timeseries,
    sites,
)
from app.method_meta import comparison_table, inference_times, kappa_matrix  # noqa: E402

sites_list = sites

FIGURES = COMPARISON_MD.parent.parent / "figures"

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
    st.subheader("Übersicht")
    st.caption(f"{n_sites} Standorte ({n_special} mit eingeschränktem Datenstand) · "
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
    st.subheader("Methodenvergleich")
    st.caption("Vier Methoden im Vergleich (Schritt 11): Komplementarität, "
               "Schwellwert-Sweep, Inferenzkosten.")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("**κ-Komplementarität (Cohen's κ, paarweise)**")
        km = kappa_matrix()
        z = [[km.get((a, b)) for b in METHODS] for a in METHODS]
        fig = go.Figure(data=go.Heatmap(
            z=z, x=list(METHODS), y=list(METHODS),
            colorscale="Blues", zmin=0, zmax=1,
            text=[[f"{v:.2f}" if v is not None else "" for v in row] for row in z],
            texttemplate="%{text}", colorbar=dict(title="κ"),
        ))
        fig.update_layout(height=400, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Niedriges κ (hell) = komplementär. Die Methoden überlappen kaum — "
                   "ein Ensemble deckt mehr ab als jede einzelne.")

    with col_r:
        st.markdown("**Inferenzkosten je Methode (Wall-Time, 5 Sites)**")
        it = inference_times()
        methods = [m for m in METHODS if m in it]
        fig2 = go.Figure()
        fig2.add_bar(name="fit (s)", x=methods, y=[it[m]["fit_s"] for m in methods],
                     marker_color="#1f77b4")
        fig2.add_bar(name="score (s)", x=methods, y=[it[m]["score_s"] for m in methods],
                     marker_color="#ff7f0e")
        fig2.update_layout(barmode="group", height=400, margin=dict(t=10, b=10),
                           yaxis_title="Sekunden")
        st.plotly_chart(fig2, width="stretch")
        st.caption("ARIMA dominiert die Kosten (Fit + Score); zscore_stl/cluster_segment "
                   "sind quasi gratis.")

    st.divider()
    st.markdown("**Schwellwert-Sweep (Flag-Rate über Aggregations-Anteil X)**")
    sweep = FIGURES / "06_sweep_flag_rates.png"
    if sweep.exists():
        st.image(str(sweep), width="stretch")
        st.caption("X_default = 0,25 (config.yaml). Gewählt, um ARIMA-Sichtbarkeit "
                   "gegenüber dem Cluster-Anker zu erhalten.")
    else:
        st.info("Sweep-Figur nicht gefunden (reports/figures/06_sweep_flag_rates.png).")

    st.divider()
    st.markdown("**Vergleichstabelle (Schritt 11)**")
    rows = comparison_table()
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        with st.expander("Rohtabelle (Markdown)"):
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

    st.subheader("Standort-Detail")
    site = st.selectbox("Standort", sites_list())
    if site in special:
        st.warning(f"⚠️ {site}: {special[site]}")

    series = load_site_timeseries(site)
    scores = load_scores_for_site(site)

    # Zeitfenster
    tmin, tmax = series.index.min().date(), series.index.max().date()
    c1, c2 = st.columns(2)
    start = c1.date_input("Von", value=tmin, min_value=tmin, max_value=tmax)
    end = c2.date_input("Bis", value=min(tmin + pd.Timedelta(days=30), tmax),
                        min_value=tmin, max_value=tmax)
    mask = (series.index.date >= start) & (series.index.date <= end)
    window = series[mask]

    st.sidebar.markdown("### Methoden")
    active = {m: st.sidebar.checkbox(m, value=(m != "autoencoder"), key=f"m_{m}")
              for m in METHODS}

    st.sidebar.markdown("### Hyperparameter (Re-Thresholding)")
    thresholds = {
        "zscore": st.sidebar.slider("Z-Score-Schwelle", 1.0, 6.0, 3.0, 0.1),
        "arima_sigma": st.sidebar.slider("ARIMA-Sigma", 1.0, 6.0, 3.0, 0.1),
        "ae_pct": st.sidebar.slider("AE-Threshold-Perzentil", 90.0, 99.9, 99.0, 0.1),
    }
    st.sidebar.caption("Verschiebt die Flag-Schwelle auf vorberechneten Scores "
                       "(keine Live-Inferenz; ARIMA-Kosten ~10 min).")

    fig = go.Figure()
    fig.add_scatter(x=window.index, y=window.values, mode="lines",
                    name="Last (kW)", line=dict(color="#888", width=1))
    wmin, wmax = window.index.min(), window.index.max()
    for m in METHODS:
        if not active[m]:
            continue
        flagged = _threshold_flags(scores, m, thresholds)
        flagged = flagged[(flagged["timestamp"] >= wmin) & (flagged["timestamp"] <= wmax)]
        if flagged.empty:
            continue
        yvals = window.reindex(flagged["timestamp"]).values
        fig.add_scatter(x=flagged["timestamp"], y=yvals, mode="markers",
                        name=f"{m} ({len(flagged)})",
                        marker=dict(color=colors[m], size=7, symbol="x"))
    fig.update_layout(height=480, margin=dict(t=10, b=10),
                      yaxis_title="kW", xaxis_title="Zeit",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Lastgang {site} · {start} bis {end} · {len(window)} 15-min-Punkte. "
               "Marker = geflaggte Anomalien je aktiver Methode (Slider-abhängig).")


PAGES = {
    "Übersicht": page_overview,
    "Methodenvergleich": page_method_comparison,
    "Standort-Detail": page_site_detail,
}


def main() -> None:
    cfg = load_config()
    b = cfg["branding"]
    st.sidebar.markdown(f"### {b['logo_placeholder']}")
    st.sidebar.title(b["title"])
    st.sidebar.caption(b["subtitle"])
    choice = st.sidebar.radio("Seite", list(PAGES.keys()))
    PAGES[choice]()


if __name__ == "__main__":
    main()
