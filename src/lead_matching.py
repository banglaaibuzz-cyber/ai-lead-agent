"""Free, deterministic matching between lead opportunities and service offers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ServiceOffer:
    name: str
    keywords: tuple[str, ...]
    description: str


OFFERS = (
    ServiceOffer("Missed-call recovery", ("missed-call", "after-hours", "call volume", "24/7"), "Capture and follow up with callers who would otherwise be lost."),
    ServiceOffer("Lead qualification", ("lead qualification", "lead generation", "financing", "quote", "estimate"), "Qualify inquiries and route high-intent prospects automatically."),
    ServiceOffer("Scheduling & dispatch", ("dispatch", "scheduling", "technician", "field-service", "same-day", "appointment"), "Reduce scheduling friction and coordinate field work."),
    ServiceOffer("Workflow automation", ("workflow automation", "manual", "spreadsheet", "reporting"), "Replace repetitive handoffs and manual reporting with repeatable workflows."),
    ServiceOffer("System integration", ("integration", "multiple systems", "data synchronization", "job-management"), "Connect systems so information moves without duplicate entry."),
    ServiceOffer("Retention automation", ("maintenance", "membership", "renewal", "retention"), "Automate reminders and follow-up that support recurring revenue."),
    ServiceOffer("Operations dashboard", ("reporting", "dashboard", "multiple locations", "fleet", "growth"), "Create a single operational view for managers and owners."),
)


def match_offers(opportunities: Iterable[str], signals: Iterable[str], limit: int = 4) -> list[dict[str, object]]:
    text = " ".join([*opportunities, *signals]).lower()
    ranked: list[tuple[int, ServiceOffer, list[str]]] = []
    for offer in OFFERS:
        hits = [keyword for keyword in offer.keywords if keyword.lower() in text]
        if hits:
            ranked.append((len(hits), offer, hits))
    ranked.sort(key=lambda item: (-item[0], item[1].name))
    return [
        {"offer": offer.name, "why": offer.description, "matched_signals": hits}
        for _, offer, hits in ranked[:limit]
    ]


def rank_lead(score: int, evidence_count: int, signal_count: int) -> tuple[str, int, str]:
    """Return tier, confidence, and a conservative next action."""
    confidence = min(100, 25 + evidence_count * 8 + signal_count * 5)
    if score >= 70 and confidence >= 65:
        return "A", confidence, "Review evidence and prioritize personalized outreach."
    if score >= 45 and confidence >= 45:
        return "B", confidence, "Validate the strongest signal before outreach."
    return "C", confidence, "Keep for research; gather stronger evidence first."
