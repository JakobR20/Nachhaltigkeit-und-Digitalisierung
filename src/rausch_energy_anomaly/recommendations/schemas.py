"""Output schema and validation for LLM-generated anomaly recommendations.

Two layers of guarantee:

1. ``RECOMMENDATION_SCHEMA`` is handed to Ollama as ``format=``. Ollama compiles
   it into a grammar and *structurally* enforces: the ``schweregrad`` enum, the
   key set (``additionalProperties: false`` + ``required``), the JSON types, and
   ``handlungsempfehlungen`` having exactly three items.

2. ``RecommendationOutput`` (Pydantic) enforces what the grammar does NOT:
   the ``confidence`` scale/range and the per-string ``maxLength`` limits. The
   grammar accepts ``maxLength`` as a hint but does not truncate, and it accepts
   any number for ``confidence`` (qwen2.5:7b emits ``85`` instead of ``0.85``;
   Phase-1 finding). These validators are ``mode="before"`` so they coerce the
   raw value before the field's own constraints run.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

URSACHE_MAX_LEN = 250
EMPFEHLUNG_MAX_LEN = 150
N_EMPFEHLUNGEN = 3

RECOMMENDATION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "schweregrad": {"type": "string", "enum": ["hoch", "mittel", "niedrig"]},
        "vermutete_ursache": {"type": "string", "maxLength": URSACHE_MAX_LEN},
        "handlungsempfehlungen": {
            "type": "array",
            "items": {"type": "string", "maxLength": EMPFEHLUNG_MAX_LEN},
            "minItems": N_EMPFEHLUNGEN,
            "maxItems": N_EMPFEHLUNGEN,
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
    "required": [
        "schweregrad",
        "vermutete_ursache",
        "handlungsempfehlungen",
        "confidence",
    ],
    "additionalProperties": False,
}


def _truncate(text: str, max_len: int) -> str:
    """Hard-truncate to ``max_len`` chars, dropping a trailing partial word."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rstrip()
    if " " in cut:
        cut = cut[: cut.rfind(" ")].rstrip()
    return cut


class RecommendationOutput(BaseModel):
    """Validated recommendation for a single anomaly."""

    schweregrad: Literal["hoch", "mittel", "niedrig"]
    vermutete_ursache: str = Field(max_length=URSACHE_MAX_LEN)
    handlungsempfehlungen: list[str]
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: float) -> float:
        # qwen2.5:7b reports confidence on a 0-100 scale ("85") despite the
        # 0.0-1.0 prompt hint; rescale, then clamp into range. Phase-1 finding.
        v = float(v)
        if v > 1.0:
            v = v / 100.0
        return max(0.0, min(1.0, v))

    @field_validator("vermutete_ursache", mode="before")
    @classmethod
    def truncate_ursache(cls, v: str) -> str:
        return _truncate(str(v), URSACHE_MAX_LEN)

    @field_validator("handlungsempfehlungen", mode="before")
    @classmethod
    def truncate_empfehlungen(cls, v: list[str]) -> list[str]:
        return [_truncate(str(item), EMPFEHLUNG_MAX_LEN) for item in v]
