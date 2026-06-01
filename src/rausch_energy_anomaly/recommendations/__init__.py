"""LLM-based recommendation layer for detected anomalies.

Public surface:
- RECOMMENDATION_SCHEMA: JSON schema passed to Ollama as ``format=``.
- RecommendationOutput: Pydantic model validating the LLM output.
- prompts: system/user prompt constants for qwen2.5:7b.
"""

from __future__ import annotations

from rausch_energy_anomaly.recommendations.prompts import (
    SYSTEM_PROMPT_PRODUCTION,
    USER_PROMPT_TEMPLATE,
)
from rausch_energy_anomaly.recommendations.schemas import (
    RECOMMENDATION_SCHEMA,
    RecommendationOutput,
)

__all__ = [
    "RECOMMENDATION_SCHEMA",
    "RecommendationOutput",
    "SYSTEM_PROMPT_PRODUCTION",
    "USER_PROMPT_TEMPLATE",
]
