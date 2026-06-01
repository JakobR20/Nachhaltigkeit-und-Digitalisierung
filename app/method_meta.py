"""Static method metadata parsed from the Phase-11 comparison table.

The kappa values and flag rates live in reports/tables/06_method_comparison.md;
parsing them here keeps a single source of truth instead of hardcoding numbers.
"""

from __future__ import annotations

import re

from app.data_access import METHODS, load_comparison_markdown


def kappa_matrix() -> dict[tuple[str, str], float]:
    """Symmetric kappa lookup {(method_a, method_b): kappa} from the comparison md."""
    md = load_comparison_markdown()
    out: dict[tuple[str, str], float] = {}
    for line in md.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3 or cells[1] not in METHODS:
            continue
        method = cells[1]
        # the "κ vs andere" cell looks like: autoencoder=0.11, cluster_segment=0.02, ...
        for m in cells:
            for other, val in re.findall(r"(\w+)=(-?\d+\.\d+)", m):
                if other in METHODS:
                    out[(method, other)] = float(val)
                    out[(other, method)] = float(val)
    for m in METHODS:
        out[(m, m)] = 1.0
    return out


def comparison_table() -> list[dict[str, str]]:
    """Parse the Phase-11 comparison table into a list of row dicts."""
    md = load_comparison_markdown()
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in md.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if cells and cells[0] == "Methode":
                header = cells
            continue
        if set("".join(cells)) <= {"-", " "}:  # separator row
            continue
        if cells and cells[0] in METHODS:
            rows.append(dict(zip(header, cells, strict=False)))
    return rows


def inference_times() -> dict[str, dict[str, float]]:
    """{method: {'fit_s': float, 'score_s': float}} from the comparison table."""
    out: dict[str, dict[str, float]] = {}
    for r in comparison_table():
        try:
            out[r["Methode"]] = {
                "fit_s": float(r["Wall-Time fit (s)"]),
                "score_s": float(r["Wall-Time score (s)"]),
            }
        except (KeyError, ValueError):
            continue
    return out
