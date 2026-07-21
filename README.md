<div align="center">

# DataMind OS

### *An AI business intelligence platform that never lets an AI make up a number.*

Upload a CSV. Get real KPIs, real forecasts, real correlations — computed the boring, reliable way with **pandas** and **statsmodels**. Then let an LLM explain what it all means in plain English, with **every claim checked against the actual data** before it ever reaches your screen.

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)

![LiteLLM](https://img.shields.io/badge/LiteLLM-multi--provider-6E56CF?style=for-the-badge)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

<br/>

**`~24.7K LOC`** · **`14 API routers`** · **`48 typed schemas`** · **`28 app routes`** · **`9 real statistical engines`**

[The one iron rule](#the-one-iron-rule) · [What it does](#what-it-actually-does) · [Architecture](#architecture) · [How I know it works](#how-i-actually-know-it-works) · [Quickstart](#quickstart) · [Tech stack](#tech-stack)

</div>

---

## Why this exists

Most "AI analytics" tools share one failure mode: ask them a hard question and they hand back a confident, well-formatted, **completely wrong** answer. The number *sounds* right. The sentence is fluent. It's just not true.

DataMind OS is built around the opposite instinct — a single constraint applied without exception:

## The one iron rule

> ### The LLM is never allowed to *compute* a number.
> ### It is only allowed to *describe* a number that deterministic code already computed and verified.

That one rule shapes everything below — why the Dashboard runs on pandas instead of prompts, why the Copilot writes **real SQL** instead of guessing, and why every AI-generated insight ships with a visible **`Verified`** / **`Unverified`** badge instead of a blanket "trust me."

Arithmetic doesn't hallucinate. So the arithmetic never touches the model.

---

## What it actually does

<table>
<tr>
<td width="50%" valign="top">

### Upload → Understand
Drop in a CSV — sales data, bank statements, SaaS subscriptions, anything. DuckDB infers the schema, and a widened, battle-tested pattern matcher auto-detects which column is revenue, which is a customer count, which is deal size, which tracks pipeline status. It understands `Revenue`, `MRR`, `ARR`, `GMV`, `Turnover`, `Net Sales` and their variants — while *correctly ignoring* a `Narration` column that just happens to contain the letters `arr`.

</td>
<td width="50%" valign="top">

### The Analytics Studio
Nine exploration tools, **all backed by real computation** — never an LLM:

`EDA` · `Statistics` · `Correlation` · `Distribution` · `Outliers` (Z-score **and** IQR) · `Trend` (regression slope + r²) · `Time Series` · `Regression` (scikit-learn) · `Forecast` (linear + Holt-Winters, with confidence bounds)

None of this touches a model. It doesn't need to.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### The Copilot
Ask a question in plain language. It doesn't guess — it writes a **real SQL query**, runs it against your data through DuckDB, and only *then* answers, with the executed query surfaced for you to audit. Ask something the data genuinely can't answer (profit margin with no cost column) and it says so, instead of inventing a number to sound helpful.

</td>
<td width="50%" valign="top">

### The Deep Insights Engine
The most ambitious piece. Instead of waiting for a question, it autonomously generates six analytical questions about your dataset, writes SQL for each through a **SELECT-only safety gate** (rejecting `DROP`, `DELETE`, `INSERT`, and a dozen other keywords), and turns the results into insights — **each re-verified against its own query** before you see it.

</td>
</tr>
</table>

### Confidence Center
A dedicated transparency dashboard showing what percentage of AI-generated insights and recommendations **actually passed verification**, with a full audit trail linking every claim back to the SQL that produced it. If the AI got something wrong, this page shows that it got something wrong. No aspirational marketing copy.

---

## Architecture

A decoupled two-service system with a deterministic core and an AI layer that sits *around* it, never *inside* the math.

```
                            ┌──────────────────────────────┐
                            │   Next.js 16 + React 19 UI    │
                            │  Studio · Copilot · Insights  │
                            │   TanStack Query · Zustand    │
                            └───────────────┬──────────────┘
                                            │  REST /api/v1
                            ┌───────────────▼──────────────┐
                            │        FastAPI Backend        │
                            │   14 routers · 48 schemas     │
                            ├───────────────────────────────┤
   ┌── Auth ────────────────┤  bcrypt + JWT (httpOnly) + slowapi rate limiting
   │                        │
   ├── Analytics Engine ────┤  pandas · numpy · scipy · statsmodels   ◄── deterministic,
   │                        │                                              LLM-free math
   ├── Regression ──────────┤  scikit-learn
   │                        │
   ├── Copilot Agent ───────┤  ReAct loop ──► DuckDB (real SQL execution)
   │                        │
   ├── Insights Engine ─────┤  LLM narration + SQL sandbox + independent re-verification
   │                        │
   ├── AI Gateway ──────────┤  LiteLLM routing · cost engine · circuit breaker · fallbacks
   │                        │
   └── PDF Generator ───────┤  reportlab + matplotlib
                            └───────────────┬──────────────┘
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
          ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
          │  SQLite / Postgres│   │   DuckDB (in-mem) │   │  Celery + Redis   │
          │  system-of-record │   │  analytical engine│   │   async AI jobs   │
          │  (SQLAlchemy ORM) │   │  over your CSVs   │   │   + Prometheus    │
          └──────────────────┘   └──────────────────┘   └──────────────────┘
                    │
                    ▼
          LiteLLM  ──►  Groq (Llama 3.1) by default
                        pluggable to Gemini / OpenAI / Anthropic
                        used ONLY for chat, summaries & insight narration
```

**The key architectural inversion:** Python deterministically computes every candidate insight (all numbers pandas-computed), a scoring function selects the strongest ones, and *only then* does the LLM write the sentence around them — the reverse of the usual "LLM writes SQL and numbers, hope for the best" pipeline.

---

## How I actually know it works

This is the part most project READMEs skip, and it's the part that matters most.

During development the platform was tested against **more than a dozen independently generated datasets** — a retail electronics chain, a SaaS subscription business, a gym membership system, several bank-statement formats, a corporate payments ledger, a digital-wallet transaction log. For each, every number the app displayed was cross-checked against a completely separate calculation, written fresh in a plain Python script that never touched the app's own code. Numbers that didn't match *exactly* were treated as bugs — not rounding quirks to wave away.

That process caught real problems:

<table>
<tr><td><b>Column-detection collision</b></td><td>Revenue detection matched the substring <code>arr</code> to catch <code>ARR</code> — and also matched the middle of <code>Narration</code>, silently breaking the entire Dashboard by trying to sum a column of sentences. <b>Fixed</b> by filtering to numeric-dtype columns <i>before</i> applying any name pattern.</td></tr>
<tr><td><b>A fabricated statistic</b></td><td>One "insight" confidently claimed a customer had a "1 in 1000" chance of a large payment "within the next week." No model in that pipeline can compute a future probability from a flat SQL query — the number came from nowhere. <b>Fixed</b> with a system-prompt ban on predictive claims, plus a language filter catching the pattern if it slips through.</td></tr>
<tr><td><b>Silent overfitting</b></td><td>A "Trend" insight was built from calendar-day averages on a sample size of one or two rows per day — accurate arithmetic dressed up as a meaningful pattern it wasn't. <b>Fixed</b> by requiring every grouped query to report its own sample size and rejecting anything built on too few rows.</td></tr>
<tr><td><b>Route shadowing</b></td><td>A generic <code>/{dataset_id}</code> route was registered before <code>/compare</code>, so every request to <code>/datasets/compare</code> was silently treated as a lookup for a dataset named "compare." <b>Fixed</b> by registering specific routes before catch-all ones.</td></tr>
</table>

None of these were found by guessing. They were found by refusing to accept "it looks right" as good enough, and checking the arithmetic every single time.

---

## Quickstart

Groq's free tier runs every AI feature in this project at **zero cost**. Without a key the platform still works fully — the analytics engine doesn't need one, and AI features degrade to clear "not configured" states instead of failing silently.

```bash
# 1 — Backend  (FastAPI · Python 3.11+)
cd ai-bi-os/backend
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # add GROQ_API_KEY and SECRET_KEY
uvicorn app.main:app --reload                           # ► http://localhost:8000

# 2 — Frontend  (Next.js 16 · React 19)
cd ai-bi-os/frontend
npm install
npm run dev                                             # ► http://localhost:3000
```

> **On Windows?** `ai-bi-os/start_servers.bat` frees ports 3000/8000 and launches both services in separate terminals.
>
> **Full stack with observability?** `docker-compose up` in `ai-bi-os/` brings up the backend, Redis, a Celery worker, Prometheus and Grafana.

### Running the tests
```bash
cd ai-bi-os/backend && python -m pytest tests/     # deterministic-math regression suite
cd ai-bi-os/frontend && npm test                   # Jest + Testing Library
```

---

## Tech stack

| Layer | Choice |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind, shadcn/ui, Framer Motion, Recharts |
| **State & data** | TanStack Query, Zustand, React Hook Form + Zod |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Analytical engine** | DuckDB (in-memory SQL over uploaded data) |
| **System-of-record** | SQLite → Postgres (`psycopg2`), object storage via S3 (`boto3`) |
| **Statistics & ML** | pandas, numpy, scipy, statsmodels, scikit-learn |
| **AI orchestration** | LiteLLM multi-provider · ReAct agent loop · MCP-style tool abstraction · AI Gateway (routing, cost engine, circuit breaker, fallbacks) |
| **LLM inference** | Groq (Llama 3.1) by default — pluggable to Gemini / OpenAI / Anthropic |
| **Async & observability** | Celery + Redis, Prometheus + Grafana |
| **Reports** | reportlab + matplotlib (server-side PDF) |
| **Auth** | bcrypt, PyJWT (httpOnly cookies), slowapi rate limiting |
| **Deploy** | Docker, Render |

---

## Roadmap — and what's honestly *not* here yet

**Shipped and working today:** deterministic analytics, the Copilot, Deep Insights, the Confidence Center, PDF export, and auth.

**Known limitations, documented rather than hidden:**

- System-of-record runs on SQLite by default (a Postgres path exists) — solid for individual/small-team use, not yet hardened for large multi-tenant scale.
- The knowledge/RAG layer grounds qualitative questions against stored business definitions; true vector embeddings are the next step.
- Regression is linear-only for now — no classification or clustering yet.
- Desktop-first UI — a responsive mobile layout is on the list.

These are documented, not hidden. That's the whole ethos.

---

## A closing thought

The interesting engineering problem here was never *"can an LLM write a paragraph about a spreadsheet."* It's *"how do you let an LLM be genuinely useful for analysis without ever trusting it to do the arithmetic."*

Everything in this repository is downstream of that question.

<div align="center">

<br/>

**Built by [Aadhar Bindal](https://github.com/Aadharbindal)**

*If this made you think differently about AI + data, a ⭐ means a lot.*

</div>
