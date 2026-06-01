"""Step C: run 3 prompt variants x 5 test anomalies against qwen2.5:7b.

Deterministic and reproducible:
- The 5 anomalies are fixed by (nr) below, selected with seed 42 in the session.
- Ollama is called with temperature 0.2 and a fixed seed per call.
- Each output is forced to RECOMMENDATION_SCHEMA (grammar) and then validated by
  the RecommendationOutput Pydantic model (confidence rescale + truncation).

Writes reports/llm_evaluation/variant_comparison.md.
Run: .venv/bin/python scripts/run_variant_comparison.py
"""

from __future__ import annotations

import csv
import json
import time
import urllib.request
from pathlib import Path

from rausch_energy_anomaly.recommendations.context import build_minimal_context
from rausch_energy_anomaly.recommendations.prompts import (
    COT_HINT,
    FEWSHOT_EXAMPLES,
    SYSTEM_PROMPT_BASE,
    USER_PROMPT_TEMPLATE,
)
from rausch_energy_anomaly.recommendations.schemas import (
    RECOMMENDATION_SCHEMA,
    RecommendationOutput,
)

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = ROOT / "reports" / "annotation" / "annotation.csv"
OUT = ROOT / "reports" / "llm_evaluation" / "variant_comparison.md"
MODEL = "qwen2.5:7b"
OLLAMA = "http://localhost:11434/api/generate"
SEED = 42
TEMPERATURE = 0.2

SELECTED_NR = ["19", "2", "1", "58", "43"]

VARIANTS = {
    "V1_minimal": SYSTEM_PROMPT_BASE,
    "V2_fewshot": SYSTEM_PROMPT_BASE + "\n\n" + FEWSHOT_EXAMPLES,
    "V3_cot": SYSTEM_PROMPT_BASE + "\n\n" + COT_HINT,
}

WEEKDAY_DE = {
    "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag",
    "Sunday": "Sonntag",
}


def load_selected() -> list[dict]:
    with open(ANNOTATION, newline="") as f:
        rows = {r["nr"]: r for r in csv.DictReader(f)}
    return [rows[nr] for nr in SELECTED_NR]


def build_user_prompt(row: dict) -> str:
    ctx = build_minimal_context(row["site"], row["timestamp"])
    if ctx.expected_kw is None:
        expected_s, diff_s, pct_s = "n/a (keine Vergleichstage)", "n/a", "n/a"
    else:
        expected_s = f"{ctx.expected_kw:.1f} (Median aus {ctx.n_vergleichstage} Vergleichstagen)"
        diff_s = f"{ctx.diff_kw:+.1f}"
        pct_s = (
            f"{ctx.diff_pct:+.1f}" if ctx.diff_pct is not None
            else "n/a (Erwartung 0 kW, jede Last ist Abweichung)"
        )
    ts = ctx.timestamp
    return USER_PROMPT_TEMPLATE.format(
        site=row["site"],
        timestamp_human=ts.strftime("%d.%m.%Y %H:%M"),
        wochentag=WEEKDAY_DE.get(row["wochentag"], row["wochentag"]),
        feiertag=row["feiertag"],
        methode=row["method"],
        segment=row["segment"],
        value_kw=f"{ctx.value_kw:.1f}",
        expected_kw=expected_s,
        diff_kw=diff_s,
        diff_pct=pct_s,
        temp="<Phase 3>",
        weather_desc="<Phase 3>",
        price_ct="<Phase 3>",
        extra_cost_eur="<Phase 3>",
    )


def call_ollama(system: str, user: str) -> tuple[RecommendationOutput, float]:
    req = {
        "model": MODEL,
        "stream": False,
        "options": {"temperature": TEMPERATURE, "seed": SEED},
        "format": RECOMMENDATION_SCHEMA,
        "system": system,
        "prompt": user,
    }
    t0 = time.perf_counter()
    r = urllib.request.urlopen(
        urllib.request.Request(OLLAMA, data=json.dumps(req).encode(),
                               headers={"Content-Type": "application/json"}),
        timeout=300)
    body = json.loads(r.read())
    wall = time.perf_counter() - t0
    parsed = RecommendationOutput.model_validate_json(body["response"])
    return parsed, wall


def main() -> None:
    rows = load_selected()
    results: dict[str, dict[str, tuple[RecommendationOutput, float]]] = {}
    user_prompts: dict[str, str] = {}

    for row in rows:
        nr = row["nr"]
        user_prompts[nr] = build_user_prompt(row)
        results[nr] = {}
        for vname, system in VARIANTS.items():
            out, wall = call_ollama(system, user_prompts[nr])
            results[nr][vname] = (out, wall)
            print(f"  nr {nr:>2} {vname:11s} {wall:5.1f}s  "
                  f"{out.schweregrad:7s} conf={out.confidence}")

    write_markdown(rows, results, user_prompts)
    print(f"\nGeschrieben: {OUT}")


def _fmt_cell(out: RecommendationOutput, wall: float) -> str:
    emp = "<br>".join(f"{i+1}. {e}" for i, e in enumerate(out.handlungsempfehlungen))
    return (f"**{out.schweregrad}** · conf {out.confidence:.2f} · {wall:.1f}s<br>"
            f"_Ursache:_ {out.vermutete_ursache}<br>_Empf.:_<br>{emp}")


def write_markdown(rows, results, user_prompts) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Prompt-Varianten-Vergleich (Schritt C)\n")
    lines.append(f"Modell: `{MODEL}` · temperature={TEMPERATURE} · seed={SEED} · "
             f"Schema grammar-erzwungen + Pydantic-validiert.\n")
    lines.append("Wetter/Strompreis/Mehrkosten sind `<Phase 3>` (Kontext-Builder liefert "
             "vorerst nur Lastgang-Fakten).\n")
    lines.append("\n## Test-Anomalien\n")
    lines.append("| nr | site | timestamp | method | segment | score |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['nr']} | {r['site']} | {r['timestamp']} | {r['method']} "
                 f"| {r['segment']} | {float(r['score']):.2f} |")

    for r in rows:
        nr = r["nr"]
        lines.append(f"\n## nr {nr} — {r['site']} · {r['method']} · {r['segment']}\n")
        lines.append("<details><summary>User-Prompt (Kontext)</summary>\n\n```")
        lines.append(user_prompts[nr])
        lines.append("```\n</details>\n")
        lines.append("| Variante | Ergebnis |")
        lines.append("|---|---|")
        for vname in VARIANTS:
            out, wall = results[nr][vname]
            lines.append(f"| {vname} | {_fmt_cell(out, wall)} |")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
