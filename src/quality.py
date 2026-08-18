"""Lead prioritization helpers.

This layer keeps ranking separate from web collection so the research engine
can evolve without changing how leads are presented.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Quality:
    priority: int
    confidence: int
    tier: str
    next_action: str


def assess(*, score: int, evidence: list[str], opportunities: list[str], url: str) -> Quality:
    """Turn raw signal strength into a conservative sales-research priority.

    Evidence is rewarded, while thin or missing evidence is deliberately
    penalized. This prevents a lead from ranking highly merely because a
    generic word appeared on a page.
    """
    evidence_points = min(25, len([x for x in evidence if len(x.strip()) >= 35]) * 5)
    opportunity_points = min(15, len(opportunities) * 3)
    domain = urlparse(url).netloc.lower()
    domain_points = 5 if domain and "." in domain else 0
    confidence = min(100, max(0, 30 + evidence_points + opportunity_points + domain_points))
    priority = min(100, max(0, int(score * 0.65 + confidence * 0.35)))

    if priority >= 75 and confidence >= 65:
        tier = "A"
        next_action = "Review evidence and prepare a highly specific, evidence-based offer."
    elif priority >= 55:
        tier = "B"
        next_action = "Verify the strongest signal before outreach."
    else:
        tier = "C"
        next_action = "Keep for research; collect stronger evidence before contacting."

    return Quality(priority=priority, confidence=confidence, tier=tier, next_action=next_action)
