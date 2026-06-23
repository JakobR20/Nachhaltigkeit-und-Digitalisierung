"""Phase 3 / Step F: dump build_full_context() for the 5 Step-C test anomalies.

Shows the exact deterministic values the LLM will see in Phase 4.
Writes reports/llm_evaluation/full_context_samples.md.
Run: .venv/bin/python scripts/dump_full_context_samples.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from rausch_energy_anomaly.recommendations.context import build_full_context
from rausch_energy_anomaly.recommendations.prompts import render_user_prompt

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = ROOT / "reports" / "annotation" / "annotation.csv"
OUT = ROOT / "reports" / "llm_evaluation" / "full_context_samples.md"
SELECTED_NR = ["19", "2", "1", "58", "43"]


def load_selected() -> list[dict]:
    with open(ANNOTATION, newline="") as f:
        rows = {r["nr"]: r for r in csv.DictReader(f)}
    return [rows[nr] for nr in SELECTED_NR]


def main() -> None:
    rows = load_selected()
    lines = ["# Full-Context-Stichproben (Phase 3, Schritt F)\n"]
    lines.append("Deterministische Werte, die das LLM in Phase 4 sieht. "
                 "Wetter = standortgenau (DWD am Site-PLZ-Centroid), Spotpreis = Stundenwert, "
                 "Mehrkosten im Code gerechnet.\n")
    lines.append("\n| nr | method | value_kw | expected_kw | diff_kw | temp °C | Wetter "
                 "| Spotpreis ct/kWh | Dauer h | Mehrkosten EUR |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    contexts = []
    for r in rows:
        c = build_full_context(r["site"], r["timestamp"], r["method"], r["segment"])
        contexts.append((r, c))
        exp = f"{c.expected_kw:.1f}" if c.expected_kw is not None else "n/a"
        temp = f"{c.temperatur_c:.1f}" if c.temperatur_c is not None else "n/v"
        lines.append(
            f"| {r['nr']} | {c.method} | {c.value_kw:.1f} | {exp} | {c.diff_kw:+.1f} "
            f"| {temp} | {c.wetter_beschreibung or 'n/v'} | {c.spotpreis_ct_pro_kwh:.2f} "
            f"| {c.dauer_h:g} | {c.mehrkosten_eur:.2f} |"
        )

    for r, c in contexts:
        lines.append(f"\n## nr {r['nr']} — {c.site} · {c.method} · {c.segment}\n")
        lines.append("```")
        lines.append(render_user_prompt(c, feiertag=r["feiertag"]))
        lines.append("```")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Geschrieben: {OUT}")


if __name__ == "__main__":
    main()
