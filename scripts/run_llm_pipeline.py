"""Phase 4: LLM recommendation pipeline over all annotated anomalies.

For each anomaly in reports/annotation/annotation.csv:
  build_full_context -> render V2 production prompt -> Ollama (qwen2.5:7b,
  format-enforced) -> Pydantic validation, with up to RETRIES attempts on
  parse/HTTP errors.

Outputs:
  reports/llm_recommendations.csv          (flat table, one row per anomaly)
  reports/llm_recommendations/{nr:03d}.json (full context + response per anomaly)

Run: .venv/bin/python scripts/run_llm_pipeline.py
"""

from __future__ import annotations

import csv
import dataclasses
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from rausch_energy_anomaly.recommendations.context import build_full_context
from rausch_energy_anomaly.recommendations.prompts import (
    SYSTEM_PROMPT_PRODUCTION,
    render_user_prompt,
)
from rausch_energy_anomaly.recommendations.schemas import (
    RECOMMENDATION_SCHEMA,
    RecommendationOutput,
)

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = ROOT / "reports" / "annotation" / "annotation.csv"
OUT_CSV = ROOT / "reports" / "llm_recommendations.csv"
OUT_JSON_DIR = ROOT / "reports" / "llm_recommendations"
MODEL = "qwen2.5:7b"
OLLAMA = "http://localhost:11434/api/generate"
SEED = 42
TEMPERATURE = 0.2
RETRIES = 3

CSV_FIELDS = [
    "nr", "site", "timestamp", "method", "schweregrad", "vermutete_ursache",
    "handlungsempfehlung_1", "handlungsempfehlung_2", "handlungsempfehlung_3",
    "confidence", "llm_model", "processing_time_s",
]


def call_with_retry(system: str, user: str) -> tuple[RecommendationOutput, float, int]:
    """Call Ollama, validate, retry on parse/HTTP error. Returns (out, wall, attempts)."""
    last_err: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
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
                timeout=120)
            body = json.loads(r.read())
            wall = time.perf_counter() - t0
            out = RecommendationOutput.model_validate_json(body["response"])
            return out, wall, attempt
        except (urllib.error.URLError, json.JSONDecodeError, ValueError, TimeoutError) as e:
            last_err = e
            time.sleep(1.0 * attempt)
    raise RuntimeError(f"failed after {RETRIES} attempts: {last_err}")


def main() -> None:
    OUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANNOTATION, newline="") as f:
        rows = list(csv.DictReader(f))

    csv_rows: list[dict] = []
    total_retries = 0
    failures: list[tuple[str, str]] = []

    for r in rows:
        nr = r["nr"]
        try:
            ctx = build_full_context(r["site"], r["timestamp"], r["method"], r["segment"])
            user = render_user_prompt(ctx, feiertag=r["feiertag"])
            out, wall, attempts = call_with_retry(SYSTEM_PROMPT_PRODUCTION, user)
        except Exception as e:  # noqa: BLE001 - record and continue, report at end
            failures.append((nr, str(e)[:80]))
            print(f"  nr {nr:>2} FAILED: {str(e)[:80]}")
            continue

        total_retries += attempts - 1
        emp = out.handlungsempfehlungen
        csv_rows.append({
            "nr": nr, "site": r["site"], "timestamp": r["timestamp"], "method": r["method"],
            "schweregrad": out.schweregrad, "vermutete_ursache": out.vermutete_ursache,
            "handlungsempfehlung_1": emp[0], "handlungsempfehlung_2": emp[1],
            "handlungsempfehlung_3": emp[2], "confidence": out.confidence,
            "llm_model": MODEL, "processing_time_s": round(wall, 2),
        })
        (OUT_JSON_DIR / f"{int(nr):03d}.json").write_text(
            json.dumps({
                "nr": nr, "annotation": r,
                "context": _ctx_to_jsonable(ctx),
                "prompt": user,
                "recommendation": out.model_dump(),
                "llm_model": MODEL, "processing_time_s": round(wall, 2),
                "attempts": attempts,
            }, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        flag = f" (retries={attempts - 1})" if attempts > 1 else ""
        print(f"  nr {nr:>2} {r['method']:15s} {wall:5.1f}s {out.schweregrad:7s} "
              f"conf={out.confidence}{flag}")

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(csv_rows)

    print(f"\nErfolgreich: {len(csv_rows)}/{len(rows)} | Retries gesamt: {total_retries} "
          f"| Fehlschläge: {len(failures)}")
    if failures:
        for nr, err in failures:
            print(f"  FAIL nr {nr}: {err}")
    print(f"CSV: {OUT_CSV}")
    print(f"JSONs: {OUT_JSON_DIR}/")


def _ctx_to_jsonable(ctx) -> dict:
    d = dataclasses.asdict(ctx)
    d["timestamp"] = str(d["timestamp"])
    return d


if __name__ == "__main__":
    main()
