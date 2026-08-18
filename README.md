# AI Lead Agent

A zero-cost-first **global B2B lead research agent**. It looks beyond obvious buying intent: it scans public business pages for operational, growth, capacity, service, and situational signals, then turns those signals into evidence-based opportunity hypotheses and reviewable outreach drafts.

## Release status

**MVP release is complete.** The repository contains the research engine, global targeting, multi-engine search, evidence capture, deduplication, opportunity matching, conservative lead ranking, browser UI, CSV/JSON export, review-only outreach drafting, optional local LLM enrichment, launchers, and automated tests.

The system is intentionally **not tied to Bangladesh or the operator's location**. The default pilot is the United States, but the UI supports the US, UK, Canada, Australia, New Zealand, Germany, Netherlands, and worldwide targeting with optional city/state/region input.

## What it does

1. Accepts a business category, market, optional location, and research goal.
2. Searches multiple public search engines instead of relying on one provider.
3. Uses several query families to find explicit needs and less-obvious situation signals.
4. Visits public result pages and extracts readable text.
5. Detects signals including hiring, manual work, spreadsheets, growth, multiple locations, dispatch, field service, technicians, after-hours service, emergency work, missed calls, estimates, maintenance plans, memberships, seasonality, call volume, integrations, and reporting.
6. Deduplicates results by canonical company domain.
7. Scores signal strength and evidence depth, then assigns a conservative A/B/C research tier and confidence score.
8. Matches evidence to practical service opportunities such as missed-call recovery, lead qualification, scheduling/dispatch, workflow automation, integrations, retention automation, and operations dashboards.
9. Shows the evidence behind the opportunity so the researcher can verify it before contacting anyone.
10. Produces a review-only outreach draft grounded in the collected evidence. **The agent never sends messages automatically.**
11. Exports research to JSON and CSV.
12. Optionally uses a locally running Ollama model for deeper analysis without API charges.
13. Runs standard-library tests and Python compilation checks in GitHub Actions.

## Run it on Windows

Requires Python 3.10+ and internet access.

1. Download/clone the repository.
2. Double-click **`run.bat`**.
3. Open `http://127.0.0.1:8000` in your browser.

Or from a terminal:

```bash
python app.py
```

## Run it on macOS/Linux

```bash
chmod +x run.sh
./run.sh
```

Then open `http://127.0.0.1:8000`.

## Command line

```bash
python src/lead_agent.py "HVAC companies in Texas, United States"
```

Multiple targets are supported:

```bash
python src/lead_agent.py "HVAC companies in Florida" "HVAC companies in Arizona"
```

Results are written to `data/leads.json` and `data/leads.csv`.

### Optional local AI enrichment

If Ollama is installed with a local model:

```bash
python src/lead_agent.py "HVAC companies in Texas, United States" --ollama
```

The deterministic research engine still works when Ollama is unavailable.

## Important limitations

- Public websites can change, block automated requests, or contain incomplete information.
- Scores are prioritization hints, not proof that a company wants to buy something.
- Evidence should always be reviewed before outreach.
- Search engines and websites can rate-limit automated requests; the agent spaces requests deliberately.
- Respect website terms, robots rules, privacy requirements, and applicable anti-spam laws. Do not use this project to collect or target sensitive personal data.
- A local run is the zero-cost default. A public always-on deployment may require a hosting service or account, even when a free tier is available.

## Project structure

- `src/lead_agent.py` — research, extraction, scoring, search, and exports.
- `src/entity.py` — company/domain identity normalization.
- `src/lead_matching.py` — deterministic service-opportunity matching and ranking.
- `src/outreach.py` — evidence-grounded draft generation; no sending.
- `app.py` — local web server/API.
- `web/index.html` — browser interface.
- `tests/` — automated tests.
- `.github/workflows/test.yml` — CI checks.
- `run.bat` / `run.sh` — beginner-friendly launchers.
