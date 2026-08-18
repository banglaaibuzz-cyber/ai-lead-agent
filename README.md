# AI Lead Agent

A zero-cost-first **global B2B lead research agent**. The system is designed to look beyond obvious buying intent: it scans public business pages for operational, growth, capacity, service, and situational signals, then converts those signals into evidence-based opportunity hypotheses.

## Current pilot

**Category:** HVAC / home-service businesses  
**Primary market:** United States  

The market is configurable and is **not tied to the operator's location**. The UI can target the US, UK, Canada, Australia, New Zealand, Germany, Netherlands, or worldwide, with an optional city/state/region.

## What the MVP does

1. Accepts a business category, market, and optional location.
2. Searches multiple public-web query families instead of relying on one buying-intent query.
3. Visits public result pages and extracts readable text.
4. Detects explicit needs and less-obvious situation signals such as hiring, manual work, spreadsheets, growth, multiple locations, dispatch, field service, after-hours service, emergency work, missed calls, estimates, maintenance plans, seasonality, call volume, integrations, and reporting.
5. Scores evidence-based opportunity signals.
6. Maps signals to practical automation/service opportunities.
7. Captures short evidence snippets so claims can be reviewed before outreach.
8. Saves results as JSON and CSV.
9. Provides a zero-dependency local browser UI through `app.py`.
10. Can optionally use a locally running Ollama model for deeper analysis, keeping the LLM portion free of API charges.

## Run the browser UI

Requires Python 3.10+ and internet access.

```bash
python app.py
```

Then open `http://127.0.0.1:8000` in a browser.

The UI defaults to **HVAC companies in the United States**, but the market and category can be changed without changing the code.

## Run from the command line

```bash
python src/lead_agent.py "HVAC companies in Texas, United States"
```

Or run multiple targets:

```bash
python src/lead_agent.py "HVAC companies in Florida" "HVAC companies in Arizona"
```

Results are written to `data/leads.json` and `data/leads.csv`.

### Optional local AI enrichment

If Ollama is installed and a model is available locally:

```bash
python src/lead_agent.py "HVAC companies in Texas, United States" --ollama
```

The agent degrades gracefully when local AI is unavailable; the deterministic evidence/signal engine still works.

## Important limitations

- Public websites can change, block automated requests, or contain incomplete information.
- Scores are prioritization hints, not proof that a company wants to buy something.
- Evidence should be reviewed before outreach.
- Respect website terms, robots rules, privacy requirements, and applicable anti-spam laws. Do not use this project to collect or target sensitive personal data.
- Free public search endpoints can have rate limits, so the agent deliberately spaces requests.

## Project status

**MVP foundation complete:** research, global market targeting, broader situation-signal detection, scoring, opportunity mapping, evidence capture, CSV/JSON export, local web UI, and optional local-LLM enrichment.

Next implementation layers are stronger source diversity, deduplication/entity resolution, configurable scoring, lead-quality/conversion scoring, buyer/service-provider matching, and an evidence-grounded outreach workflow.
