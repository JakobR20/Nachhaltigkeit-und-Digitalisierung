"""Baut notebooks/04_segments.ipynb (nbformat). Einmal-Generator.

Segment-Feature-Exploration + Silhouette/Elbow als Vorbereitung des Clusterings
(v4 §5 Schritt 5). Fit/Silhouette nur auf Train-Slice (2023–2024), incomplete
Segment-Tage aus dem Fit ausgeschlossen (aber im Parquet behalten).
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


# --------------------------------------------------------------------------- #
md(
    """
# 04 – Segment-Features & Silhouette (Vorbereitung Clustering)

Berechnet pro Site die Tageszeit-Segment-Features (`features/segments.py`), persistiert
sie und untersucht via Silhouette/Elbow, welche Clusterzahl `k` je Clustering plausibel
ist. **Fit/Silhouette nur auf dem Train-Slice (2023–2024)** – das Parquet enthält alle
Jahre, aber k-Wahl und Cluster-Zentren werden ohne Test-Leakage bestimmt.
"""
)

code(
    """
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rausch_energy_anomaly.ingestion import rlm_loader as loader  # noqa: E402
from rausch_energy_anomaly.features.segments import compute_segment_features  # noqa: E402

FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
PROCESSED = ROOT / "data" / "processed"

cfg = yaml.safe_load((ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))
SEGMENTS = cfg["clustering"]["segmente"]["segments"]
FEATURES = cfg["clustering"]["segmente"]["features_per_segment"]
K_SEG = cfg["clustering"]["segmente"]["k_values"]
K_DAILY = cfg["clustering"]["tagesprofile"]["k_values"]
SEG_NAMES = [s["name"] for s in SEGMENTS]
TRAIN_END = pd.to_datetime("2024-12-31").date()   # Train-Slice: 2023–2024
SEED = cfg["general"]["seed"]

plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (11, 4), "axes.grid": True, "grid.alpha": 0.3})


def savefig(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150, bbox_inches="tight")
    print("gespeichert:", FIG.name + "/" + name)
"""
)

# --- Block 1: Segment-Features berechnen + persistieren -------------------- #
md(
    """
## 1. Segment-Features pro Site berechnen
Baumärkte laden, flache Zähler (vmax < 1 kW) ausschließen, je Site die Segment-Features.
"""
)

code(
    """
df = loader.load_category("Baumärkte")
vmax = df.groupby(level="meter_id")["value_kw"].max()
solid_ids = sorted(vmax[vmax >= 1.0].index)
print("Solide Zähler:", len(solid_ids))

parts = []
for sid in solid_ids:
    sdf = df.xs(sid, level="meter_id")
    feat = compute_segment_features(sdf, sid, SEGMENTS, FEATURES)
    feat["site"] = sid
    parts.append(feat.set_index("site", append=True).reorder_levels(["site", "date"]))
seg = pd.concat(parts).sort_index()
seg.to_parquet(PROCESSED / "segment_features.parquet")
print("segment_features:", seg.shape)
seg.head(3)
"""
)

# --- Block 2: Train-Slice + incomplete-Maske ------------------------------- #
md(
    """
## 2. Train-Slice (2023–2024) und Vollständigkeits-Maske

`fit`/Silhouette nutzen **nur** Tage bis `TRAIN_END` und schließen je Segment die
`*_incomplete`-Tage aus. Das Parquet bleibt vollständig (alle Jahre, inkl. incomplete).
"""
)

code(
    """
dates = seg.index.get_level_values("date")
train_mask = pd.Series([d <= TRAIN_END for d in dates], index=seg.index)
print("Zeilen gesamt:", len(seg), "| im Train-Slice:", int(train_mask.sum()))
inc_rate = {s: float(seg[f"{s}_incomplete"].mean()) for s in SEG_NAMES}
print("Incomplete-Rate je Segment:", {k: round(v, 4) for k, v in inc_rate.items()})
"""
)

# --- Block 3: Visualisierung ----------------------------------------------- #
md(
    """
## 3. Visualisierung
"""
)

code(
    """
# Verteilung des mean je Segment (Form/Größe der Tageszeiten)
fig, ax = plt.subplots()
data = [seg[f"{s}_mean"].dropna().values for s in SEG_NAMES]
ax.boxplot(data, labels=SEG_NAMES, showfliers=False)
ax.set_title("Verteilung mittlere Leistung je Segment (Baumärkte)")
ax.set_xlabel("Segment")
ax.set_ylabel("mean Leistung [kW]")
savefig(fig, "04_segment_mean_verteilung.png")
plt.show()
"""
)

code(
    """
# Incomplete-Rate über die Zeit (DST-/Ausfalltage sichtbar) – Summe je Tag über Segmente
inc_cols = [f"{s}_incomplete" for s in SEG_NAMES]
by_day = seg[inc_cols].groupby(level="date").sum().sum(axis=1)
fig, ax = plt.subplots(figsize=(13, 3.5))
ax.plot(list(by_day.index), by_day.values, lw=0.6)
ax.set_title("Incomplete Segment-Tage über die Zeit (Summe über Sites × Segmente)")
ax.set_xlabel("Datum")
ax.set_ylabel("# incomplete")
savefig(fig, "04_incomplete_ueber_zeit.png")
plt.show()
"""
)

# --- Block 4: Silhouette/Elbow --------------------------------------------- #
md(
    """
## 4. Silhouette + Elbow zur k-Wahl

- **Tagesprofile** (96-dim): pro Zeile (site, day) normiert (Form) → ein Clustering.
- **Pro Segment**: 4 Features (mean/max/std/slope), **pro Segment getrennt standardisiert**
  (sonst clustert man Tag vs. Nacht statt Form innerhalb der Tageszeit). Vier Clusterings.

`silhouette_score` mit `sample_size` (O(n²)-Schutz).
"""
)

code(
    """
def elbow_silhouette(X: np.ndarray, ks: list[int], title: str, fname: str) -> int:
    inertia, sil = [], []
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X)
        inertia.append(km.inertia_)
        ssize = min(2000, len(X))
        sil.append(silhouette_score(X, km.labels_, sample_size=ssize, random_state=SEED))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6))
    a1.plot(ks, inertia, marker="o"); a1.set_title(f"Elbow – {title}"); a1.set_xlabel("k"); a1.set_ylabel("Inertia")
    a2.plot(ks, sil, marker="o", color="tab:green"); a2.set_title(f"Silhouette – {title}"); a2.set_xlabel("k"); a2.set_ylabel("Silhouette")
    savefig(fig, fname)
    plt.show()
    best = int(ks[int(np.argmax(sil))])
    print(f"{title}: bestes k (Silhouette) = {best}")
    return best
"""
)

code(
    """
# (a) Tagesprofile 96-dim, Train-Slice, zeilenweise normiert
ts = df.loc[solid_ids].index.get_level_values("timestamp")
tmp = pd.DataFrame({
    "site": df.loc[solid_ids].index.get_level_values("meter_id"),
    "date": ts.date,
    "slot": ts.hour * 4 + ts.minute // 15,
    "value": df.loc[solid_ids]["value_kw"].values,
})
daily = tmp.pivot_table(index=["site", "date"], columns="slot", values="value").dropna(thresh=90)
daily = daily[[d <= TRAIN_END for d in daily.index.get_level_values("date")]]
row_mean = daily.mean(axis=1)
daily = daily.apply(lambda col: col.fillna(row_mean))   # Rest-NaN je Zeile mit Zeilenmittel
Xd = daily.to_numpy()
Xd = (Xd - Xd.mean(1, keepdims=True)) / (Xd.std(1, keepdims=True) + 1e-9)
best_daily = elbow_silhouette(Xd, K_DAILY, "Tagesprofile (96-dim)", "04_silhouette_tagesprofile.png")
"""
)

code(
    """
# (b) Pro Segment: 4 Features, Train-Slice, incomplete raus, PRO SEGMENT standardisiert
best_seg = {}
for s in SEG_NAMES:
    cols = [f"{s}_{f}" for f in FEATURES]
    mask = train_mask & ~seg[f"{s}_incomplete"].astype(bool)
    sub = seg.loc[mask, cols].dropna()
    Xs = StandardScaler().fit_transform(sub.to_numpy())
    best_seg[s] = elbow_silhouette(Xs, K_SEG, f"Segment '{s}'", f"04_silhouette_segment_{s}.png")
print("Beste k je Clustering:", {"tagesprofile": best_daily, **best_seg})
"""
)

# --- Block 5: Befunde + Merge-Skizze --------------------------------------- #
md(
    """
## 5. Befunde & wie die fünf Clusterings zusammengeführt werden

**Ergebnisse (Train-Slice 2023–2024, 23 solide Baumärkte, 23.242 Segment-Tage gesamt, davon 14.703 im Train):**
- **Silhouette-bevorzugtes k:** Tagesprofil **2**, nachts **2**, vormittag **2**, mittag **4**, nachmittag **2**.
- Silhouette favorisiert also überwiegend eine **grobe Zwei-Cluster-Trennung** (typisch vs. atypisch); nur das **Mittag**-Segment zeigt feinere Struktur (k=4). Die finale k-Wahl trifft Schritt 6 (ggf. mit fachlicher statt rein silhouette-getriebener Begründung, da k=2 sehr grob ist).
- **Incomplete-Rate ≈ 0,1 %** je Segment → bei den (sauberen) ZRV-Baumärkten verändert der Incomplete-Ausschluss den Fit kaum; die Mechanik ist v. a. für DST-/Ausfalltage und die kWh-Lastgang-Sites relevant.

**Entscheidungen (dokumentiert):**
- **Fit nur auf Train-Slice 2023–2024**, k-Wahl/Zentren ohne Test-Leakage; das Parquet
  `segment_features.parquet` enthält alle Jahre (inkl. 2025–2026) für die spätere Diagnose.
- **Incomplete Segment-Tage** (`*_incomplete = True`, v. a. DST-/Ausfalltage) sind aus dem
  Fit ausgeschlossen, bleiben aber im Parquet erhalten.
- **Pro-Segment-Standardisierung** (getrennt je Segment), damit die Cluster Form-Unterschiede
  *innerhalb* einer Tageszeit abbilden, nicht den trivialen Tag-vs-Nacht-Niveauunterschied.

**Fünf Clusterings nebeneinander – geplante Zusammenführung (Schritt 6 / `diagnosis`):**
- Es entstehen **fünf** Cluster-Modelle: 1× Tagesprofil (96-dim) + 4× Segment.
- Pro (site, day) liefert jedes Modell **ein Cluster-Label** → fünf Labels je Tag.
- Das **Tagesprofil-Label** beschreibt den *Gesamtcharakter* des Tages (welcher Typ-Tag),
  die **vier Segment-Labels** lokalisieren, *welche Tageszeit* abweicht.
- In `diagnosis/anomaly_classifier.py` werden die Labels **nicht** zu einem Modell verschmolzen,
  sondern als Kontext kombiniert: Anomalie-Score (aus ARIMA/AE) + das auffällige
  Segment-Label → Aussage „Nachmittag, Cluster 3 = ungewöhnlich hoch". Das Tagesprofil-Label
  dient als Quervalidierung (untypischer Tag insgesamt?). So bleiben die Clusterings verbunden
  statt fünf isolierter Ergebnisse.
"""
)

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

out = Path(__file__).resolve().parent / "04_segments.ipynb"
nbf.write(nb, out)
print("geschrieben:", out, "| Zellen:", len(cells))
