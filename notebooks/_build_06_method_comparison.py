"""Baut notebooks/06_method_comparison.ipynb (nbformat). Einmal-Generator.

Schritt 11 — Methodenvergleich auf den drei portierten Methoden (zscore_stl,
arima, cluster_segment). X-Sweep der Anteils-Aggregation, κ-Heatmaps,
Inferenzzeit-Mikrobenchmark, Precision aus Annotation (sobald da),
Sieger-/Ensemble-Empfehlung, Vergleichstabelle in reports/tables/.
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells: list = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text: str) -> None:
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


md(
    """
# 06 — Methodenvergleich (Schritt 11)

Drei Methoden im Vergleich: **`zscore_stl`** (Punkt-Outlier auf STL-Residual),
**`arima`** (lokal-prognostische Abweichung pro Peer-Cluster) und
**`cluster_segment`** (Form-/Segment-untypisch, native Segment-Tag-Granularität).
Der Autoencoder ist aus dem Vergleich genommen (Stage-A-Befund:
macOS-Hang in `model.fit` auf realer Datengröße; Modul + Driver bleiben für
Linux/CI im Code — siehe `reports/methodology.md`).

Vorgehen:

1. **Cluster-Anker** — Test-Flag-Rate aus dem aktuellen
   `anomaly_scores.parquet` ableiten (nicht hartcodiert).
2. **X-Sweep** der Anteils-Aggregation auf `(site, date, segment)` —
   `aggregate_to_segment_day(threshold_pct=…)` über
   `{0.0, 0.10, 0.25, 0.50, 0.75}`. `0.0` reproduziert das alte „any".
3. **X_default wählen** — kleinster X, bei dem die Punkt-Methoden in
   die Größenordnung Cluster-Anker fallen (Ratio 0,5–2).
4. **κ-Heatmap** über mehrere X — bleibt Komplementarität erhalten?
5. **Inferenzzeit** auf 5 Sites (Loader-Lauf einmal).
6. **Precision** aus `reports/annotation/annotation.csv` — heute noch leer;
   Notebook läuft trotzdem durch, Empfehlung ist solange „Ensemble bis
   Annotation". Sobald Felix & Jakob ihre Labels einspielen, re-evaluiert
   `recommend_strategy()` ohne Code-Änderung.
7. **Vergleichstabelle** als Markdown in `reports/tables/06_method_comparison.md`.

Nach diesem Lauf: `X_default` in `config/config.yaml`
(`comparison.aggregation_threshold_pct`) und in `reports/methodology.md`
festschreiben.
"""
)

code(
    """
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from rausch_energy_anomaly.evaluation.method_comparison import (
    DEFAULT_TRAIN_END,
    EXCLUDE_SITES,
    aggregate_to_segment_day,
    compare_at_thresholds,
    inference_timing,
    load_default_threshold_pct,
    precision_from_annotation,
    recommend_strategy,
    summary_table,
)

_ROOT = Path.cwd().resolve()
if _ROOT.name == "notebooks":
    _ROOT = _ROOT.parent
print("project root:", _ROOT)

scores = pd.read_parquet(_ROOT / "data" / "processed" / "anomaly_scores.parquet")
print(
    f"scores: {len(scores)} rows, methods: {sorted(scores['method'].unique())}, "
    f"sites: {scores['site'].nunique()}"
)
"""
)

md(
    """
## 1 — Cluster-Anker: Test-Flag-Rate aus dem aktuellen Parquet

`cluster_segment` ist nativ Segment-Tag-granular; ihre Test-Flag-Rate
ist der Anker für die X-Wahl der Punkt-Methoden — direkt aus dem Parquet
abgeleitet, nicht aus dem Smoke-Lauf erinnert.
"""
)

code(
    """
ts_all = pd.to_datetime(scores["timestamp"])
scores_ex23 = scores[~scores["site"].isin(EXCLUDE_SITES)].copy()
cluster_rows = scores_ex23[scores_ex23["method"] == "cluster_segment"].copy()
cluster_rows["date"] = pd.to_datetime(cluster_rows["timestamp"]).dt.date
cluster_test = cluster_rows[cluster_rows["date"] > DEFAULT_TRAIN_END]
cluster_anchor = float(cluster_test["flag"].astype(bool).mean())
print(f"Cluster-Distanz Test-Flag-Rate: {cluster_anchor * 100:.2f}%  (n={len(cluster_test)})")
"""
)

md(
    """
## 2 — X-Sweep: Flag-Raten je Methode (Train / Test)

`compare_at_thresholds` aggregiert die Punkt-Methoden je X auf Segment-Tag
und berechnet Flag-Rate (Train ≤ 2024, Test 2025+). Cluster-Distanz ist X-
invariant (nativ Segment-Tag).
"""
)

code(
    """
SWEEP_X = (0.0, 0.10, 0.25, 0.50, 0.75)
flag_rates, pairwise = compare_at_thresholds(scores, thresholds=SWEEP_X)
flag_rates_pivot = flag_rates.pivot(
    index="threshold_pct", columns="method", values="flag_rate_test"
)
print("Flag-Rate Test je Methode × X:")
print((flag_rates_pivot * 100).round(3).to_string())
"""
)

code(
    """
fig, ax = plt.subplots(figsize=(9, 5))
colors = {"zscore_stl": "tab:blue", "arima": "tab:orange", "cluster_segment": "tab:green"}
for method in flag_rates_pivot.columns:
    ax.plot(
        flag_rates_pivot.index,
        flag_rates_pivot[method] * 100,
        marker="o",
        label=method,
        color=colors.get(method),
    )
ax.axhline(
    cluster_anchor * 100,
    color="gray",
    linestyle="--",
    linewidth=0.8,
    label=f"cluster anchor ({cluster_anchor * 100:.2f}%)",
)
ax.set_xlabel("threshold_pct (Anteil flagged points im Segment)")
ax.set_ylabel("Flag-Rate Test [%]")
ax.set_yscale("log")
ax.set_title("X-Sweep — Test-Flag-Rate je Methode")
ax.legend()
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout()
out = _ROOT / "reports" / "figures" / "06_sweep_flag_rates.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=120)
plt.show()
print(f"saved: {out.relative_to(_ROOT)}")

# Persist the sweep values so the dashboard can render them interactively
# (Plotly) without recomputing compare_at_thresholds (~28 s).
sweep_csv = _ROOT / "reports" / "tables" / "06_sweep_flag_rates.csv"
sweep_csv.parent.mkdir(parents=True, exist_ok=True)
(flag_rates_pivot * 100).reset_index().to_csv(sweep_csv, index=False)
print(f"saved: {sweep_csv.relative_to(_ROOT)}")
"""
)

md(
    """
## 3 — X-Default-Wahl

Kriterium: **kleinster X, bei dem `zscore_stl` UND `arima` Test-Flag-Rate
zwischen 0,5× und 2× des Cluster-Ankers liegen** — vergleichbare Detektor-
Sensitivität, kein „Aggregations-Artefakt mehr". Zu klein → die any-
Aufblähung dominiert (arima ~30 %, zscore ~14 % am alten Smoke-Lauf).
Zu groß → die Methoden flaggen kaum mehr etwas, Vergleich verarmt.
"""
)

code(
    """
def _ratio(rate):
    return rate / cluster_anchor if cluster_anchor > 0 else float("nan")


cand_rows = []
for x in [x for x in SWEEP_X if x > 0]:
    row = flag_rates_pivot.loc[x]
    zs = float(row.get("zscore_stl", float("nan")))
    ar = float(row.get("arima", float("nan")))
    ratios = [_ratio(zs), _ratio(ar)]
    in_band = all(0.5 <= r <= 2.0 for r in ratios)
    cand_rows.append(
        {
            "threshold_pct": x,
            "zscore_test_%": zs * 100,
            "arima_test_%": ar * 100,
            "zs_ratio_to_anchor": ratios[0],
            "ar_ratio_to_anchor": ratios[1],
            "in_band": in_band,
        }
    )
cand_df = pd.DataFrame(cand_rows)
print(cand_df.round(3).to_string(index=False))

in_band = cand_df[cand_df["in_band"]]
if len(in_band):
    heuristic_x = float(in_band["threshold_pct"].min())
    heuristic_rationale = (
        f"Heuristik: X={heuristic_x} ist der kleinste Sweep-Wert, bei dem zscore_stl "
        f"UND arima in 0,5×..2× des Cluster-Ankers ({cluster_anchor * 100:.2f}%) liegen."
    )
else:
    # Heuristik: kleinster Abstand zur Anker-Rate (fallback)
    cand_df["max_distance_to_band"] = cand_df.apply(
        lambda r: max(
            abs(r["zs_ratio_to_anchor"] - 1.0),
            abs(r["ar_ratio_to_anchor"] - 1.0),
        ),
        axis=1,
    )
    heuristic_x = float(cand_df.loc[cand_df["max_distance_to_band"].idxmin(), "threshold_pct"])
    heuristic_rationale = (
        f"Heuristik: kein Sweep-Wert in [0,5×..2×]-Band; nächst-bester nach Anker-Nähe "
        f"wäre X={heuristic_x} — ABER die Heuristik berücksichtigt nicht, dass dabei "
        "eine Methode (ARIMA) auf 0 % Flag-Rate kollabiert."
    )
print(heuristic_rationale)

# Override: methodische Entscheidung aus config.yaml (post-Sweep-Wahl, vgl. methodology.md).
config_x = load_default_threshold_pct()
if config_x is not None:
    chosen_x = float(config_x)
    rationale = (
        f"X_default = {chosen_x} aus config.yaml (comparison.aggregation_threshold_pct). "
        "Methodische Entscheidung nach dem Sweep: ARIMA-Sichtbarkeit erhalten "
        f"(Ratio 1,64 zum Cluster-Anker bei X=0,25). Die Z-Score/ARIMA-Asymmetrie "
        "(zscore_test 3,90 % vs. ARIMA 1,05 % vs. Cluster 0,64 % — kein gemeinsames X "
        "kalibriert beide Punkt-Methoden auf dieselbe Flag-Rate) wird als "
        "eigenständiger Befund ausgewiesen."
    )
else:
    chosen_x = heuristic_x
    rationale = (
        heuristic_rationale + " (Kein Override in config.yaml gesetzt — Wahl noch offen.)"
    )

print(f"\\n→ X_default = {chosen_x}")
print(rationale)
"""
)

md(
    """
## 4 — κ-Heatmap über Sweep

Sinkt κ bei höherem X gegen 0 → Methoden werden disjunkt → Ensemble-Pfad
sinnvoll. Bleibt κ hoch → Methoden konvergieren → Sieger-Pfad denkbar,
sofern auch Precision differenziert.
"""
)

code(
    """
def kappa_heatmap(pairwise, x, ax):
    sub = pairwise[pairwise["threshold_pct"] == x]
    methods = sorted(set(sub["method_a"]) | set(sub["method_b"]))
    mat = pd.DataFrame(np.nan, index=methods, columns=methods)
    for _, row in sub.iterrows():
        mat.loc[row["method_a"], row["method_b"]] = row["kappa"]
        mat.loc[row["method_b"], row["method_a"]] = row["kappa"]
    for m in methods:
        mat.loc[m, m] = 1.0
    sns.heatmap(
        mat.astype(float),
        annot=True,
        fmt=".2f",
        vmin=-0.2,
        vmax=1.0,
        cmap="RdBu_r",
        center=0.4,
        ax=ax,
        cbar=False,
    )
    ax.set_title(f"κ bei X = {x}")


fig, axes = plt.subplots(1, len(SWEEP_X), figsize=(4.2 * len(SWEEP_X), 4))
for ax, x in zip(axes, SWEEP_X, strict=False):
    kappa_heatmap(pairwise, x, ax)
fig.tight_layout()
out = _ROOT / "reports" / "figures" / "06_kappa_heatmap.png"
fig.savefig(out, dpi=120)
plt.show()
print(f"saved: {out.relative_to(_ROOT)}")
"""
)

md(
    """
## 5 — Inferenzzeit (5 Sites, ein Loader-Lauf)

Loader-Pass einmal (~45 s), pro Methode wird `fit + score` gemessen.
**Wird einmalig ausgeführt** und in die Vergleichstabelle übernommen —
kein erneuter Lauf bei Notebook-Re-Renders. ARIMA ist der dominante
Block (auto_arima 3× über die Peer-Gruppen).
"""
)

code(
    """
timing = inference_timing(category="Baumärkte")
print(timing.to_string(index=False))
"""
)

md(
    """
## 6 — Precision aus Annotation

Strenge Lesart (siehe `precision_from_annotation`-Docstring):
`plausibel_anomal → TP`, `erklärbar → FP`, `unklar → ausgeschlossen`. Solange
die `label`-Spalten leer sind, liefert die Funktion einen leeren DataFrame
und die Empfehlung bleibt „Ensemble bis Annotation".
"""
)

code(
    """
precision = precision_from_annotation()
if len(precision):
    print(precision.to_string(index=False))
else:
    print("(noch keine Annotationen — Felix & Jakob füllen heute Abend)")
"""
)

md(
    """
## 7 — Vergleichstabelle + Empfehlung
"""
)

code(
    """
md_table = summary_table(
    flag_rates, pairwise, x_default=chosen_x, timing_df=timing, precision_df=precision
)
print(md_table)

tables_dir = _ROOT / "reports" / "tables"
tables_dir.mkdir(parents=True, exist_ok=True)
out = tables_dir / "06_method_comparison.md"
out.write_text(
    f"# Methodenvergleich (Schritt 11) — X_default = {chosen_x}\\n\\n"
    f"Cluster-Anker (Test-Flag-Rate): {cluster_anchor * 100:.2f}%\\n\\n"
    f"X-Wahl-Rationale: {rationale}\\n\\n"
    f"{md_table}\\n",
    encoding="utf-8",
)
print(f"\\nsaved: {out.relative_to(_ROOT)}")
"""
)

code(
    """
strategy, label, rationale_rec = recommend_strategy(
    precision, pairwise, x_default=chosen_x
)
print(f"strategy   = {strategy}")
print(f"label      = {label}")
print(f"rationale  = {rationale_rec}")
"""
)

md(
    """
## 8 — Was als Nächstes ins Repo geht

- `config/config.yaml` — `comparison.aggregation_threshold_pct: <chosen_x>` ablegen.
- `reports/methodology.md` — Befund-Abschnitt „Methodenvergleich (Schritt 11)"
  ergänzen: Sweep-Tabelle, X-Wahl-Begründung, Strategie-Empfehlung, Verweis
  auf `reports/tables/06_method_comparison.md` und die zwei Figuren.
- Nach Annotation: dieses Notebook neu ausführen — Precision wird automatisch
  eingelesen, `recommend_strategy` re-evaluiert.
"""
)

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
out = Path(__file__).resolve().parent / "06_method_comparison.ipynb"
nbf.write(nb, out)
print("geschrieben:", out, "| Zellen:", len(cells))
