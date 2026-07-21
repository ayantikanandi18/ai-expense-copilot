# AI Expense & Invoice Copilot

A small Flask + Postgres app that parses receipts/invoices with an LLM, classifies each line item into an expense category with a stated rationale, projects next month's spend per category, and exposes a webhook for automation tools (n8n/Zapier) to feed it headlessly.

Built as a direct response to a fintech AI/automation engineer job description — the feature list below maps to that JD's specific bullets rather than being generic.

## Why this exists / how it maps to the role

| JD requirement | Where it shows up here |
|---|---|
| Automate financial workflows (invoicing, forecasting, expense classification) | `app/pipeline.py` (parse → classify → store), `app/forecasting.py` (next-month projection) |
| NLP applications: document parsing, summarization | `app/ai/llm_client.py` `parse_document()` |
| AI wrapper apps over Groq/OpenAI/Anthropic/Gemini | `app/ai/llm_client.py` — narrow interface, only Groq wired up today, isolated so swapping providers is a contained change |
| Secure, scalable AI pipelines; monitor & retrain | `app/models.py` `AuditLog` — every LLM call is logged (input excerpt + output) for review |
| Python / Flask / PostgreSQL monolith | The whole app |
| Tailwind CSS | Compiled via the Tailwind CLI (`tailwind.config.js` → `app/static/css/output.css`), not the CDN script — the CDN build explicitly warns against production use |
| n8n / Zapier automation | `POST /webhooks/ingest` — see below |
| QuickBooks Intuit API exposure | `app/integrations/quickbooks.py` — real OAuth2 + Purchase-sync code, **not connected to a live account** (see that file's docstring) |
| GDPR/CCPA-aware, explainable | `app/ai/privacy.py` (PII redaction before any LLM call), per-classification `rationale` stored and shown, document delete endpoint |

## Running it

```bash
cp .env.example .env        # then fill in GROQ_API_KEY at minimum
docker compose up -d        # starts Postgres — Docker Desktop must be running
pip install -r requirements.txt
npm install                 # Tailwind CLI (dev dependency only)
npm run build:css           # compiles app/static/css/output.css
python run.py
```

Open http://localhost:5000/. Paste a sample invoice/receipt as text (or upload a .txt/.pdf) on the dashboard.

If Docker isn't available, set `DATABASE_URL=sqlite:///dev.db` in `.env` instead — everything else works unchanged against SQLite for local testing.

If you change any Tailwind classes in `app/templates/`, re-run `npm run build:css` (or `npm run watch:css` while iterating) to regenerate the compiled stylesheet.

### Demo data

`python scripts/seed_demo_data.py` populates the dashboard with clearly-labeled synthetic documents/line items/monthly totals (4 months, 6 categories) so the charts, KPIs, and forecasts have something to show instead of being blank on a first run. It's safe to re-run — it wipes and re-seeds. Every seeded document's raw text is prefixed `[SYNTHETIC DEMO DATA — not real]`; this is fixture data, not real Groq output.

## Wiring the webhook from n8n or Zapier

`POST /webhooks/ingest` with a JSON body `{"text": "<raw invoice/receipt text>"}` runs the exact same parse+classify pipeline as the manual upload form, headlessly.

- **n8n**: an "HTTP Request" node (POST, JSON body with a `text` field built from whatever upstream node reads the email attachment / Sheet row / Drive file) pointed at this URL.
- **Zapier**: a "Webhooks by Zapier — POST" action with the same JSON shape, triggered off a Gmail/Drive/Sheets trigger.

```bash
curl -X POST http://localhost:5000/webhooks/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "Acme Cloud Hosting Invoice #4471\nDate: 2026-06-01\nAWS Compute: $340.00\nAWS Storage: $85.00\nTotal: $425.00"}'
```

## Known limitations (stated plainly, not hidden)

- **No OCR** — only text-based PDFs and plain text are supported, not scanned images.
- **Forecast is a simple linear-trend line**, not a proper time-series model — appropriate given how little historical data a demo has, and easy to explain honestly in an interview.
- **QuickBooks integration is not live** — the OAuth2 flow and Purchase-sync call are real, correct code against Intuit's documented API, but require your own Intuit developer sandbox credentials to actually execute.
- **PII redaction is regex-based**, catching common SSN/credit-card/email/phone patterns before text reaches the LLM — a data-minimization gesture, not a certified compliance solution.
- The Groq system prompts are constrained to only extract/classify what's explicitly in the given text — they're instructed never to invent amounts, vendors, or line items.

## Stack

Flask, Flask-SQLAlchemy, PostgreSQL (via Docker Compose), Groq (`llama-3.3-70b-versatile`), Tailwind CSS (compiled via CLI), Chart.js (CDN), `pypdf` for PDF text extraction.
