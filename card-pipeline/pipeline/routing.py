"""Confidence-based routing — the heart of the cost-aware design.

Given a tier's extraction result, decide whether the record is resolved or must
escalate, and to which tier. Two independent gates:

  1. Textual confidence < threshold  -> escalate to the LLM text tier (cheap).
     The text is too sparse to pin the card down.
  2. Parallel/finish is visually undetermined (`parallel_status == "uncertain"`)
     -> escalate to the CV retrieval tier, *even if* textual confidence is high.
     This is the ambiguous-image case: everything reads fine, but only the photo
     reveals whether it's the base or a parallel.

Gate 1 is checked first because the text tier is cheaper than the image tiers.
(Later builds add Tier 2/3/4; for now escalation just records the intended next
tier and the record lands in Silver as `pending`.)
"""
from __future__ import annotations

import config as C

# Where each gate sends a record. Kept here so the escalation map is explicit.
NEXT_TIER_LOW_CONF = "llm_text"
NEXT_TIER_PARALLEL = "cv_retrieval"


def route(extraction: dict, threshold: float | None = None) -> dict:
    """Return a routing decision for one extraction result."""
    threshold = C.CONFIDENCE_THRESHOLD if threshold is None else threshold
    conf = extraction["confidence"]
    pstatus = extraction["parallel_status"]

    if conf < threshold:
        return _escalate(NEXT_TIER_LOW_CONF, f"text confidence {conf} < {threshold}")
    if pstatus == "uncertain":
        return _escalate(NEXT_TIER_PARALLEL, "parallel undetermined from text")
    return {
        "decision": "resolved",
        "next_tier": None,
        "status": "resolved_text",
        "reason": "resolved by text alone",
    }


def _escalate(next_tier: str, reason: str) -> dict:
    return {
        "decision": "escalate",
        "next_tier": next_tier,
        "status": f"pending_{next_tier}",
        "reason": reason,
    }
