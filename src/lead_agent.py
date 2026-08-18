#!/usr/bin/env python3
"""Zero-cost global B2B lead research agent."""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from .entity import canonical_domain
    from .lead_matching import match_offers, rank_lead
except ImportError:
    from entity import canonical_domain
    from lead_matching import match_offers, rank_lead

UA = "Mozilla/5.0 (compatible; AILeadAgent/0.3; +https://github.com/banglaaibuzz-cyber/ai-lead-agent)"

PAIN_SIGNALS = {
    "hiring": (8, "Hiring activity can indicate capacity or process pressure."), "manual": (9, "Manual work suggests an automation opportunity."), "spreadsheet": (8, "Spreadsheet-heavy work can be a workflow opportunity."), "slow": (6, "Slow response or delivery language suggests an efficiency gap."), "backlog": (7, "A backlog suggests unmet operational demand."), "growth": (7, "Growth can create new process, reporting, or automation needs."), "expanding": (8, "Expansion often creates repeatable operational problems."), "new location": (7, "New locations create setup and coordination work."), "multiple locations": (8, "Multiple locations can create coordination and reporting complexity."), "customer support": (8, "Support volume can create automation and knowledge-base opportunities."), "lead generation": (7, "Lead-generation activity can create qualification and follow-up opportunities."), "recruiting": (7, "Recruiting activity can indicate repetitive screening and scheduling work."), "booking": (6, "Booking workflows may be improved with automation."), "appointment": (6, "Appointment workflows may be improved with automation."), "inventory": (6, "Inventory work can create monitoring and reporting opportunities."), "reporting": (6, "Reporting work can often be automated or streamlined."), "integration": (8, "Integration language suggests disconnected systems."), "multiple systems": (9, "Multiple systems suggest integration or workflow opportunities."), "api": (5, "API activity may indicate a system that can be connected or automated."), "24/7": (6, "24/7 service can create scheduling, routing, and after-hours workflow needs."), "after hours": (7, "After-hours service can create missed-call and dispatch opportunities."), "emergency": (6, "Emergency service creates time-sensitive routing and communication needs."), "same day": (6, "Same-day service creates scheduling and dispatch pressure."), "estimate": (6, "Estimate workflows can be streamlined with qualification and follow-up."), "quote": (5, "Quote activity can create follow-up and conversion opportunities."), "dispatch": (9, "Dispatch activity suggests routing and scheduling complexity."), "field service": (8, "Field-service operations often involve coordination and data handoffs."), "job management": (7, "Job-management activity can expose workflow and integration opportunities."), "maintenance plan": (7, "Maintenance plans can benefit from recurring reminders and retention workflows."), "membership": (6, "Membership programs can create renewal and retention automation opportunities."), "financing": (5, "Financing offers can create qualification and follow-up workflow needs."), "reviews": (4, "Review volume can indicate reputation-management and response workload."), "service area": (5, "A broad service area can increase routing and scheduling complexity."), "fleet": (6, "Fleet operations can create monitoring and coordination needs."), "technicians": (6, "A technician workforce creates scheduling and field-operations needs."), "seasonal": (6, "Seasonality can create forecasting, staffing, and demand-management pressure."), "peak season": (7, "Peak-season language suggests temporary capacity and scheduling pressure."), "missed call": (9, "Missed calls can represent lost revenue and follow-up opportunities."), "call volume": (7, "High call volume can create triage and response-time pressure."),
}

OFFER_MAP = {"hiring": "candidate screening or recruiting workflow automation", "recruiting": "candidate screening or recruiting workflow automation", "manual": "workflow automation", "spreadsheet": "spreadsheet-to-dashboard/workflow automation", "customer support": "support triage and knowledge-base automation", "lead generation": "lead qualification and follow-up automation", "booking": "booking and reminder automation", "appointment": "appointment and reminder automation", "reporting": "automated reporting/dashboarding", "integration": "system integration or data synchronization", "multiple systems": "system integration or data synchronization", "inventory": "inventory monitoring/reporting automation", "growth": "operations automation and reporting", "expanding": "operations automation for scale", "multiple locations": "multi-location operations/reporting automation", "24/7": "after-hours intake and routing automation", "after hours": "missed-call capture and follow-up automation", "emergency": "urgent lead triage and dispatch workflow automation", "same day": "scheduling and dispatch automation", "estimate": "estimate intake and follow-up automation", "quote": "quote follow-up and conversion automation", "dispatch": "dispatch, routing, and scheduling automation", "field service": "field-service workflow and data synchronization", "job management": "job-management workflow integration", "maintenance plan": "maintenance reminder and retention automation", "membership": "membership renewal and retention automation", "financing": "financing-lead qualification and follow-up automation", "reviews": "review monitoring and response workflow", "service area": "service-area routing and scheduling automation", "fleet": "fleet monitoring and operations reporting", "technicians": "technician scheduling and field operations automation", "seasonal": "seasonal demand forecasting and staffing workflow", "peak season": "peak-season intake, scheduling, and capacity automation", "missed call": "missed-call capture and instant follow-up automation", "call volume": "call triage and response automation"}

@dataclass
class Lead:
    name: str
    url: str
    query: str
    title: str = ""
    snippet: str = ""
    score: int = 0
    priority: str = "C"
    confidence: int = 0
    next_action: str = "Keep for research; gather stronger evidence first."
    signals: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    matched_offers: list[dict[str, object]] = field(default_factory=list)
    contact_hint: str = ""
    source_count: int = 1


def fetch(url: str, timeout: int = 12) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8"})
    with urlopen(req, timeout=timeout) as r:
        raw = r.read(500_000); charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def clean_text(raw: str) -> str:
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))).strip()


def search_web(query: str, limit: int = 8) -> list[dict[str, str]]:
    text = fetch("https://html.duckduckgo.com/html/?q=" + quote_plus(query)); results = []
    pattern = re.compile(r'(?s)<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>')
    for href, title_html in pattern.findall(text):
        if href.startswith("//"): href = "https:" + href
        results.append({"title": clean_text(title_html), "url": html.unescape(href)})
        if len(results) >= limit: break
    for item in results:
        m = re.search(r"uddg=([^&]+)", item["url"])
        if m: item["url"] = unquote(m.group(1))
    return results


def root_name(url: str) -> str:
    return canonical_domain(url)


def analyze_text(text: str) -> tuple[int, list[str], list[str], list[str]]:
    low = text.lower(); score = 0; signals = []; opportunities = []; evidence = []; seen_offers = set()
    for phrase, (points, explanation) in PAIN_SIGNALS.items():
        if phrase not in low: continue
        score += points; signals.append(f"{phrase}: {explanation}")
        offer = OFFER_MAP.get(phrase)
        if offer and offer not in seen_offers: opportunities.append(offer); seen_offers.add(offer)
        idx = low.find(phrase); evidence.append(text[max(0, idx - 100):min(len(text), idx + len(phrase) + 180)])
    return min(score, 100), signals[:12], opportunities[:8], evidence[:10]


def research_target(target: str, max_results: int = 8, delay: float = 1.0) -> list[Lead]:
    queries = [f'"{target}" hiring OR recruiting OR careers', f'"{target}" manual OR spreadsheet OR automation OR integration', f'"{target}" growth OR expanding OR "new location" OR "multiple locations"', f'"{target}" "customer support" OR "lead generation" OR booking OR appointment', f'"{target}" dispatch OR "field service" OR technicians OR "job management"', f'"{target}" "after hours" OR emergency OR "same day" OR "missed call"', f'"{target}" estimate OR quote OR "maintenance plan" OR membership OR financing', f'"{target}" seasonal OR "peak season" OR "call volume" OR fleet']
    leads: dict[str, Lead] = {}
    for query in queries:
        try: results = search_web(query, max_results)
        except Exception as exc: print(f"Search failed for {query!r}: {exc}", file=sys.stderr); continue
        for result in results:
            url, host = result["url"], root_name(result["url"])
            if not host or host in {"duckduckgo.com", "google.com", "bing.com", "youtube.com"}: continue
            lead = leads.setdefault(host, Lead(name=host, url=url, query=query, title=result["title"], contact_hint=urljoin(url, "/contact")))
            if query != lead.query: lead.source_count += 1
            try:
                page = clean_text(fetch(url)); score, signals, opps, evidence = analyze_text(page)
                lead.score = max(lead.score, score)
                for x in signals:
                    if x not in lead.signals: lead.signals.append(x)
                for x in opps:
                    if x not in lead.opportunities: lead.opportunities.append(x)
                for x in evidence:
                    if x not in lead.evidence: lead.evidence.append(x)
                lead.matched_offers = match_offers(lead.opportunities, lead.signals)
                lead.priority, lead.confidence, lead.next_action = rank_lead(lead.score, len(lead.evidence), len(lead.signals))
            except Exception as exc: lead.evidence.append(f"Could not fetch page: {exc}")
            time.sleep(delay)
    priority_order = {"A": 0, "B": 1, "C": 2}
    return sorted(leads.values(), key=lambda x: (priority_order[x.priority], -x.score, -x.confidence, -x.source_count))


def ollama_enrich(leads: list[Lead], model: str = "llama3.2:3b") -> None:
    prompt = "You are a practical B2B opportunity researcher. Based ONLY on this evidence, return 3 concise bullets: likely problem, service/product opportunity, and why now. Do not invent facts. Evidence:\n{}"
    for lead in leads:
        if not lead.evidence: continue
        payload = json.dumps({"model": model, "prompt": prompt.format("\n".join(lead.evidence[:5])), "stream": False}).encode()
        try:
            req = Request("http://localhost:11434/api/generate", data=payload, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=30) as r: data = json.loads(r.read().decode())
            response = data.get("response", "").strip()
            if response: lead.opportunities.insert(0, "Local-LLM analysis: " + response)
        except Exception: return


def save_json(leads: Iterable[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps([asdict(x) for x in leads], indent=2, ensure_ascii=False), encoding="utf-8")


def save_csv(leads: Iterable[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "url", "title", "score", "priority", "confidence", "next_action", "opportunities", "matched_offers", "signals", "evidence", "contact_hint", "source_count", "query"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for lead in leads:
            row = asdict(lead)
            for k in ("opportunities", "signals", "evidence"): row[k] = " | ".join(row[k])
            row["matched_offers"] = " | ".join(x["offer"] for x in row["matched_offers"])
            w.writerow({k: row[k] for k in fields})


def main() -> None:
    p = argparse.ArgumentParser(description="Zero-cost global B2B lead research agent")
    p.add_argument("target", nargs="+", help="industry, niche, market, location, or company type to research"); p.add_argument("--results", type=int, default=6); p.add_argument("--delay", type=float, default=1.0); p.add_argument("--ollama", action="store_true"); p.add_argument("--model", default="llama3.2:3b"); p.add_argument("--out", default="data/leads")
    args = p.parse_args(); leads = []
    for target in args.target: print(f"Researching: {target}"); leads.extend(research_target(target, args.results, args.delay))
    if args.ollama: ollama_enrich(leads, args.model)
    save_json(leads, Path(args.out + ".json")); save_csv(leads, Path(args.out + ".csv"))
    for i, lead in enumerate(leads[:20], 1): print(f"{i:>2}. [{lead.priority}] {lead.name:<35} score={lead.score:>3} confidence={lead.confidence:>3}")
    print(f"\nSaved {len(leads)} leads to {args.out}.json and {args.out}.csv")

if __name__ == "__main__": main()
