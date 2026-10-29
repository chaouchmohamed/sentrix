"""Rule -> attack stage mapping (SRS 5.2). Order matters for the timeline."""
from __future__ import annotations

STAGE_ORDER = ["Reconnaissance", "Credential attack", "Initial access",
               "Discovery and execution", "Persistence", "Tool transfer"]

RULE_TO_STAGE = {
    "R06": "Reconnaissance",
    "R01": "Credential attack",
    "R02": "Credential attack",
    "R03": "Initial access",
    "R04": "Discovery and execution",
    "R05": "Tool transfer",
}


def stage_of(rule_id: str) -> str | None:
    return RULE_TO_STAGE.get(rule_id)


def ordered(stages: set[str]) -> list[str]:
    return [s for s in STAGE_ORDER if s in stages]
