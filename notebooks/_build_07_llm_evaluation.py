"""Auswertung der qualitativen LLM-Empfehlungs-Bewertung (Phase 5).

Liest reports/llm_recommendations.csv (Spalte ``quality_label``, ggf. zusätzliche
Reviewer-Spalten ``quality_label_*``) und schreibt eine Markdown-Zusammenfassung
nach reports/tables/07_llm_evaluation.md: Verteilung gut/akzeptabel/schlecht gesamt
und pro Methode, Bezug zur Modell-Konfidenz, und — falls zwei Reviewer-Spalten
vorhanden sind — die Übereinstimmungsrate.

Robust gegen den Vor-Phase-5-Zustand (alle Labels leer): meldet dann nur, dass noch
nichts zu bewerten ist, und schreibt keine irreführenden Zahlen.

Run: .venv/bin/python notebooks/_build_07_llm_evaluation.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports" / "llm_recommendations.csv"
OUT = ROOT / "reports" / "tables" / "07_llm_evaluation.md"
VALID = ("gut", "akzeptabel", "schlecht")
METHODS = ("zscore_stl", "arima", "cluster_segment", "autoencoder")


def main() -> None:
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []

    reviewer_cols = [c for c in fields if c == "quality_label" or c.startswith("quality_label_")]
    consolidated = "quality_label" if "quality_label" in fields else None

    labelled = [r for r in rows if consolidated and r.get(consolidated, "").strip()]
    invalid = [r for r in labelled if r[consolidated].strip() not in VALID]

    lines = ["# Qualitative LLM-Empfehlungs-Bewertung (Phase 5)\n"]

    if not labelled:
        lines.append("> Noch keine Bewertungen vorhanden — `quality_label` ist leer. "
                     "Anleitung: `reports/llm_recommendations_REVIEW.md`.\n")
        _write(lines)
        print(f"Noch nichts bewertet. Platzhalter geschrieben: {OUT}")
        return

    if invalid:
        bad = sorted({r[consolidated].strip() for r in invalid})
        lines.append(f"> ⚠️ {len(invalid)} Zeilen mit ungültigem Label {bad} "
                     f"— erwartet: {VALID}. Diese sind unten ausgeschlossen.\n")

    valid_rows = [r for r in labelled if r[consolidated].strip() in VALID]
    n = len(valid_rows)
    dist = Counter(r[consolidated].strip() for r in valid_rows)
    lines.append(f"\nBewertet: **{n}/{len(rows)}**.\n")
    lines.append("\n## Verteilung gesamt\n")
    lines.append("| Label | n | Anteil |")
    lines.append("|---|---|---|")
    for lab in VALID:
        c = dist.get(lab, 0)
        lines.append(f"| {lab} | {c} | {100 * c / n:.0f} % |")

    lines.append("\n## Pro Methode\n")
    lines.append("| Methode | n | gut | akzeptabel | schlecht |")
    lines.append("|---|---|---|---|---|")
    by_m: dict[str, Counter] = defaultdict(Counter)
    for r in valid_rows:
        by_m[r["method"]][r[consolidated].strip()] += 1
    for m in METHODS:
        c = by_m.get(m)
        if not c:
            continue
        tot = sum(c.values())
        lines.append(f"| {m} | {tot} | {c.get('gut', 0)} | "
                     f"{c.get('akzeptabel', 0)} | {c.get('schlecht', 0)} |")

    # Konfidenz vs. Urteil
    lines.append("\n## Modell-Konfidenz nach Urteil\n")
    lines.append("| Label | mittlere confidence |")
    lines.append("|---|---|")
    for lab in VALID:
        confs = [float(r["confidence"]) for r in valid_rows if r[consolidated].strip() == lab]
        if confs:
            lines.append(f"| {lab} | {sum(confs) / len(confs):.3f} |")

    # Inter-Rater, falls zwei echte Reviewer-Spalten existieren
    per_reviewer = [c for c in reviewer_cols if c.startswith("quality_label_")]
    if len(per_reviewer) >= 2:
        a, b = per_reviewer[0], per_reviewer[1]
        both = [r for r in rows if r.get(a, "").strip() and r.get(b, "").strip()]
        if both:
            agree = sum(1 for r in both if r[a].strip() == r[b].strip())
            pct = 100 * agree / len(both)
            lines.append(f"\n## Inter-Rater ({a} vs. {b})\n")
            lines.append(f"Übereinstimmung: **{agree}/{len(both)} = {pct:.0f} %**.")

    _write(lines)
    print(f"Geschrieben: {OUT}  ({n}/{len(rows)} bewertet)")


def _write(lines: list[str]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
