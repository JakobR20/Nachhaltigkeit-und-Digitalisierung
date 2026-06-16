"""Ensemble coverage analysis on the validated anomaly set (the 66 annotated).

Method membership per anomaly = primary `method` ∪ `also_flagged_by` from
reports/annotation/annotation.csv. This is the validated, repo-documented
definition (Top-20 overlap on exact (site, timestamp); see
export_annotation.py). NO recall is computed — there is no full ground truth,
only the validated top-candidate set.

Writes reports/tables/ensemble_coverage.csv.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = ROOT / "reports" / "annotation" / "annotation.csv"
OUT = ROOT / "reports" / "tables" / "ensemble_coverage.csv"

METHODS = ["zscore_stl", "arima", "cluster_segment", "autoencoder"]
VALID_LABEL = "plausibel_anomal"


def methods_of(row: dict) -> set[str]:
    """All methods that flagged this anomaly: primary ∪ also_flagged_by."""
    ms = {row["method"].strip()}
    extra = row["also_flagged_by"].strip()
    if extra:
        ms |= {m.strip() for m in extra.split(",") if m.strip()}
    return ms


def main() -> None:
    with open(ANNOTATION, newline="") as f:
        rows = list(csv.DictReader(f))
    validated = [r for r in rows if r["label"].strip() == VALID_LABEL]
    n_total = len(validated)

    membership = [methods_of(r) for r in validated]

    # (a) flagged per method
    flagged = {m: sum(1 for s in membership if m in s) for m in METHODS}
    # (c) unique contribution (only this method)
    unique = {m: sum(1 for s in membership if s == {m}) for m in METHODS}
    # (b) ensemble = union (>=1 method)
    ensemble = sum(1 for s in membership if len(s) >= 1)
    # (d) overlap distribution
    overlap = Counter(len(s) for s in membership)
    # (e) precision per method + union (all validated => 100% by construction)
    precision = {m: (1.0 if flagged[m] else None) for m in METHODS}
    precision_union = 1.0 if ensemble else None

    # --- console output ---
    print("== Schritt 0: Definition ==")
    print(f"Validierte Menge = {n_total} Anomalien (label={VALID_LABEL}).")
    print("Methoden-Zugehörigkeit = method ∪ also_flagged_by aus annotation.csv")
    print("Hinweis: Die 66 sind per Konstruktion bereits die priorisierte Vereinigung")
    print("der Top-20 je Methode → 'Ensemble (Union)' = Gesamtzahl ist erwartungsgemäß")
    print("trivial = n. Aussagekräftig sind Pro-Methode-Abdeckung + eindeutige Beiträge.\n")

    print("== (a) geflaggte validierte Anomalien je Methode ==")
    for m in METHODS:
        print(f"  {m:16s} {flagged[m]:3d}")
    print(f"\n== (b) Ensemble (Union, >=1 Methode) == {ensemble}")
    print("\n== (c) eindeutiger Beitrag (nur diese Methode) ==")
    for m in METHODS:
        print(f"  {m:16s} {unique[m]:3d}")
    print("\n== (d) Überlappungsverteilung (von genau k Methoden geflaggt) ==")
    for k in (1, 2, 3, 4):
        print(f"  von {k} Methode(n): {overlap.get(k, 0)}")
    print("\n== (e) Precision (validierte Menge) ==")
    for m in METHODS:
        p = precision[m]
        print(f"  {m:16s} {'100%' if p == 1.0 else 'n/a'} (n={flagged[m]})")
    print(f"  UNION            {'100%' if precision_union == 1.0 else 'n/a'} (n={ensemble})")

    best = max(flagged, key=lambda m: flagged[m])
    print("\n== Kernaussage ==")
    print(f"Ensemble (Union): {ensemble} validierte Treffer vs. beste Einzelmethode "
          f"{best}: {flagged[best]} → +{ensemble - flagged[best]} zusätzliche.")
    print("KEIN Recall (keine vollständige Ground-Truth, nur validierte Top-Kandidaten).")
    print("Limitation: also_flagged_by erfasst nur exakte (site,timestamp)-Überlappung "
          "innerhalb der Top-20; Cross-Granularität (cluster=Segment-Tag vs. Punkt) "
          "bleibt unerfasst → eindeutige Beiträge sind eine Obergrenze.")

    # --- CSV ---
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "flagged_validated", "unique_contribution",
                    "precision_validated"])
        for m in METHODS:
            w.writerow([m, flagged[m], unique[m],
                        "100%" if precision[m] == 1.0 else "n/a"])
        w.writerow(["ENSEMBLE_UNION", ensemble, "-",
                    "100%" if precision_union == 1.0 else "n/a"])
        w.writerow([])
        w.writerow(["overlap_k_methods", "count", "", ""])
        for k in (1, 2, 3, 4):
            w.writerow([k, overlap.get(k, 0), "", ""])
        w.writerow([])
        w.writerow(["note", "no recall — no full ground truth, validated top "
                    "candidates only", "", ""])
        w.writerow(["note", "overlap via also_flagged_by captures only exact "
                    "(site,timestamp) matches within each method's Top-20; "
                    "cross-granularity overlap (cluster=segment-day vs point methods) "
                    "is not captured → unique contributions are an upper bound", "", ""])
    print(f"\nGeschrieben: {OUT}")


if __name__ == "__main__":
    main()
