"""Cost computation for anomalies.

The per-incident cost (diff_kw * dauer_h * spot_price) is already persisted in the
recommendation JSONs by the pipeline. Here we only add the annual projection and
the edge-case flags the frontend needs to switch rendering.
"""

from __future__ import annotations

from typing import Any

from app.models.schemas import CostBreakdown

DAYS_PER_YEAR = 365


def is_underconsumption(diff_kw: float | None) -> bool:
    return diff_kw is not None and diff_kw < 0


def is_negative_price(spotpreis_ct: float | None) -> bool:
    return spotpreis_ct is not None and spotpreis_ct < 0


def annual_projection(mehrkosten_eur: float | None) -> float | None:
    """365 x single-incident cost (simple assumption); None passes through."""
    if mehrkosten_eur is None:
        return None
    return round(mehrkosten_eur * DAYS_PER_YEAR, 2)


def build_cost_breakdown(ctx: dict[str, Any]) -> CostBreakdown:
    diff = ctx.get("diff_kw")
    dauer = ctx.get("dauer_h", 0.0)
    spot = ctx.get("spotpreis_ct_pro_kwh")
    cost = ctx.get("mehrkosten_eur")
    kwh = round(diff * dauer, 2) if diff is not None else None
    return CostBreakdown(
        diff_kw=diff,
        dauer_h=dauer,
        diff_kwh=kwh,
        spotpreis_ct=spot,
        mehrkosten_eur=cost,
        jahreskosten_eur=annual_projection(cost),
        is_underconsumption=is_underconsumption(diff),
        is_negative_price=is_negative_price(spot),
    )
