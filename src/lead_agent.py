#!/usr/bin/env python3
"""Zero-cost lead research agent.

Uses public web search + website text extraction + transparent scoring.
Optional Ollama support adds local LLM analysis without an API bill.
"""
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
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (compatible; AILeadAgent/0.1; +https://github.com/banglaaibuzz-cyber/ai-lead-agent)"

PAIN_SIGNALS = {
    "hiring": (8, "Hiring activity can indicate capacity or process pressure."),
    "manual": (9, "Manual work suggests an automation opportunity."),
    "spreadsheet": (8, "Spreadsheet-heavy work can be a workflow opportunity."),
    "slow": (6, "Slow response or delivery language suggests an efficiency gap."),
    "backlog": (7, "A backlog suggests unmet operational demand."),
    "growth": (7, "Growth can create new process, reporting, or automation needs."),
    "expanding": (8, "Expansion often creates repeatable operational problems."),
    "new location": (7, "New locations create setup and coordination work."),
    "customer support": (8, "Support volume can create automation and knowledge-base opportunities."),
    "lead generation": (7, "Lead-generation activity can create qualification and follow-up opportunities."),
    "recruiting": (7, "Recruiting activity can indicate repetitive screening and scheduling work."),
    "booking": (6, "Booking workflows may be improved with automation."),
    "appointment": (6, "Appointment workflows may be improved with automation."),
    "inventory": (6, "Inventory work can create monitoring and reporting opportunities."),
    "reporting": (6, "Reporting work can often be automated or streamlined."),
    "integration": (8, "Integration language suggests disconnected systems."),
    "multiple systems": (9, "Multiple systems suggest integration or workflow opportunities."),
    "api": (5, "API activity may indicate a system that can be connected or automated."),
}

OFFER_MAP = {
    "hiring": "candidate screening or recruiting workflow automation",
    "recruiting": "candidate screening or recruiting workflow automation",
    "manual": "workflow automation",
    "spreadsheet": "spreadsheet-to-dashboard/workflow automation",
    "customer support": "support triage and knowledge-base automation",
    "lead generation": "lead qualification and follow-up automation",
    "booking": "booking and reminder automation",
    "appointment": "appointment and reminder automation",
    "reporting": "automated reporting/dashboarding",
    "integration": "system integration or data synchronization",
    "multiple systems": "system integration or data synchronization",
    "inventory": "inventory monitoring/reporting automation",
    "growth": "operations automation and reporting",
    "expanding": "operations automation for scale",
}

@dataclass
class Lead:
    name: str
    url: str
    query: str
    title: str = ""
    snippet: str = ""
    score: int = 0
    signals: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    contact_hint: str = ""


def fetch(url: str, timeout: int = 12) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8"})
    with urlopen(req, timeout=timeout) as r:
        raw = r.read(500_000)
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def clean_text(raw: str) -> str:
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def search_web(query: str, limit: int = 8) -> list[dict[str, str]]:
    """Search DuckDuckGo's public HTML endpoint; no API key required."""
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    text = fetch(url)
    results = []
    pattern = re.compile(r'(?s)<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>')
    for href, title_html in pattern.findall(text):
        title = clean_text(title_html)
        if href.startswith("//"):
            href = "https:" + href
        results.append({"title": title, "url": html.unescape(href)})
        if len(results) >= limit:
            break
    # DDG sometimes wraps URLs in redirect links. Extract the actual URL when possible.
    for item in results:
        m = re.search(r"uddg=([^&]+)", item["url"])
        if m:
            from urllib.parse import unquote
            item["url"] = unquote(m.group(1))
    return results


def root_name(url: str) -> str:
    host = urlparse(url).netloc.lower().split(":")[0]
    return host.removeprefix("www.")


def analyze_text(text: str) -> tuple[int, list[str], list[str], list[str]]:
    low = text.lower()
    score = 0
    signals, opportunities, evidence = [], [], []
    seen_offers = set()
    for phrase, (points, explanation) in PAIN_SIGNALS.items():
        if phrase in low:
            score += points
            signals.append(f"{phrase}: {explanation}")
            offer = OFFER_MAP.get(phrase)
            if offer and offer not in seen_offers:
                opportunities.append(offer)
                seen_offers.add(offer)
            # Capture a short evidence window for human review.
            idx = low.find(phrase)
            start = max(0, idx - 100)
            evidence.append(text[start:min(len(text), idx + len(phrase) + 180)])
    return min(score, 100), signals[:10], opportunities[:6], evidence[:8]


def contact_hint(url: str, text: str) -> str:
    for path in ("/contact", "/about", "/careers"):
        candidate = urljoin(url, path)
        if candidate != url:
            return candidate
    return url


def research_target(target: str, max_results: int = 8, delay: float = 1.0) -> list[Lead]:
    queries = [
        f'"{target}" hiring OR recruiting OR careers',
        f'"{target}" manual OR spreadsheet OR automation OR integration',
        f'"{target}" growth OR expanding OR "new location"',
        f'"{target}" "customer support" OR "lead generation" OR booking',
    ]
    leads: dict[str, Lead] = {}
    for query in queries:
        try:
            results = search_web(query, max_results)
        except Exception as exc:
            print(f"Search failed for {query!r}: {exc}", file=sys.stderr)
            continue
        for result in results:
            url = result["url"]
            host = root_name(url)
            if not host or host in {"duckduckgo.com", "google.com", "bing.com", "youtube.com"}:
                continue
            lead = leads.setdefault(host, Lead(name=host, url=url, query=query))
            lead.title = lead.title or result["title"]
            try:
                page = clean_text(fetch(url))
                score, signals, opps, evidence = analyze_text(page)
                lead.score = max(lead.score, score)
                for x in signals:
                    if x not in lead.signals: lead.signals.append(x)
                for x in opps:
                    if x not in lead.opportunities: lead.opportunities.append(x)
                for x in evidence:
                    if x not in lead.evidence: lead.evidence.append(x)
                lead.contact_hint = contact_hint(url, page)
            except Exception as exc:
                lead.evidence.append(f"Could not fetch page: {exc}")
            time.sleep(delay)
    return sorted(leads.values(), key=lambda x: x.score, reverse=True)


def ollama_enrich(leads: list[Lead], model: str = "llama3.2:3b") -> None:
    """Optional local LLM enrichment. Does nothing if Ollama is unavailable."""
    prompt_template = (
        "You are a practical B2B opportunity researcher. Based ONLY on this evidence, "
        "return 3 concise bullets: likely problem, service/product opportunity, and why now. "
        "Do not invent facts. Evidence:\n{}"
    )
    for lead in leads:
        if not lead.evidence:
            continue
        payload = json.dumps({"model": model, "prompt": prompt_template.format("\n".join(lead.evidence[:5])), "stream": False}).encode()
        try:
            req = Request("http://localhost:11434/api/generate", data=payload, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            lead.opportunities.insert(0, "Local-LLM analysis: " + data.get("response", "").strip())
        except Exception:
            return


def save_json(leads: Iterable[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(x) for x in leads], indent=2, ensure_ascii=False), encoding="utf-8")


def save_csv(leads: Iterable[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "url", "title", "score", "opportunities", "signals", "evidence", "contact_hint", "query"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for lead in leads:
            row = asdict(lead)
            for k in ("opportunities", "signals", "evidence"): row[k] = " | ".join(row[k])
            w.writerow({k: row[k] for k in fields})


def main() -> None:
    p = argparse.ArgumentParser(description="Zero-cost web lead research agent")
    p.add_argument("target", nargs="+", help="industry, niche, location, or company type to research")
    p.add_argument("--results", type=int, default=6, help="search results per query")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between page requests")
    p.add_argument("--ollama", action="store_true", help="try local Ollama for deeper analysis")
    p.add_argument("--model", default="llama3.2:3b")
    p.add_argument("--out", default="data/leads", help="output file prefix")
    args = p.parse_args()
    leads: list[Lead] = []
    for target in args.target:
        print(f"Researching: {target}")
        leads.extend(research_target(target, args.results, args.delay))
    if args.ollama: ollama_enrich(leads, args.model)
    save_json(leads, Path(args.out + ".json")); save_csv(leads, Path(args.out + ".csv"))
    for i, lead in enumerate(leads[:20], 1):
        print(f"{i:>2}. {lead.name:<35} score={lead.score:>3}  {lead.opportunities[0] if lead.opportunities else 'review manually'}")
    print(f"\nSaved {len(leads)} leads to {args.out}.json and {args.out}.csv")

if __name__ == "__main__":
    main()
