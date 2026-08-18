"""Evidence-grounded outreach drafting. Never sends messages automatically."""
from __future__ import annotations


def draft_outreach(lead: dict, sender_offer: str | None = None) -> dict[str, str]:
    name = str(lead.get("name", "the team"))
    evidence = [str(x).strip() for x in lead.get("evidence", []) if str(x).strip()]
    opportunities = [str(x).strip() for x in lead.get("opportunities", []) if str(x).strip()]
    offer = sender_offer or (opportunities[0] if opportunities else "workflow improvement")
    proof = evidence[0][:240] if evidence else "public information suggests there may be an operational opportunity worth reviewing"
    subject = f"Idea for {name}"
    body = (
        f"Hi {name},\n\n"
        f"I came across your business while researching operational workflows in your market. "
        f"One public signal I noticed was: {proof}\n\n"
        f"That made me think there may be an opportunity around {offer}. "
        f"I may be missing context, so I wanted to ask rather than assume.\n\n"
        f"Would it be useful if I shared a short idea for how this could be streamlined?\n\n"
        f"Best,\n[Your name]"
    )
    return {"subject": subject, "body": body}
