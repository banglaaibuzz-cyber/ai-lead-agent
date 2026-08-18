# AI Lead Agent

A zero-cost-first B2B lead research agent. It does more than search for obvious buying intent: it scans public business pages for operational signals such as hiring, manual work, spreadsheets, growth, support load, booking, reporting, integrations, and expansion, then converts those signals into practical opportunity hypotheses.

## What the MVP does

1. Accepts an industry, niche, location, or company type.
2. Runs several public web searches around different problem signals.
3. Visits public result pages and extracts readable text.
4. Scores evidence-based opportunity signals.
5. Produces suggested service/product opportunities and evidence snippets.
6. Saves results as JSON and CSV.
7. Can optionally use a locally running Ollama model for deeper analysis, so the LLM portion can remain free of API charges.

## Run it

Requires Python 3.10+ and internet access.

```bash
python src/lead_agent.py "dental clinics in Dhaka"
```

Try a few broader searches:

```bash
python src/lead_agent.py "small accounting firms" "local ecommerce brands"
```

Results are written to `data/leads.json` and `data/leads.csv`.

### Optional local AI enrichment

If Ollama is installed and a model is available locally:

```bash
python src/lead_agent.py "dental clinics in Dhaka" --ollama
```

The agent is designed to degrade gracefully when local AI is unavailable; the deterministic signal engine still works.

## Important limitations

- Public websites can change, block automated requests, or contain incomplete information.
- Scores are prioritization hints, not proof that a company wants to buy something.
- Evidence should be reviewed before outreach.
- Respect website terms, robots rules, privacy requirements, and applicable anti-spam laws. Do not use this project to collect or target sensitive personal data.

## Project status

**MVP complete:** research, signal detection, scoring, opportunity mapping, evidence capture, CSV/JSON export, and optional local-LLM enrichment.

Next planned layers are a small browser UI, stronger source diversity, deduplication, configurable scoring, and an outreach-drafting workflow that keeps claims grounded in the collected evidence.
