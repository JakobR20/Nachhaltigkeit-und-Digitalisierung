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
)
from app.method_meta import comparison_table, inference_times, kappa_matrix  # noqa: E402

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


PAGES = {
    "Übersicht": page_overview,
    "Methodenvergleich": page_method_comparison,
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
