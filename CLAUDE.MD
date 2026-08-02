# Cinturão do FABR Project

## Overview

This is a Visualization-based app primarely focused on showing results and Basic/Advanced Stats about FABR, Futebol Americano Brasileiro. The idea is to fully showcase Cinturão do FABR, which is basically The Unofficial Football World Championships but for American Football in Brazil

There's already an app implemented at app/ folder where there's an UI with some data in app/data/ that already showcases what I roughly want. This was an early prototipe, before Claude, done with mostly Streamlit, and limited because of it aswell. You should use this as a guide, but you don't need to really follow what's inside of it because it has mostly a different view from what I want from this new website

## Development Process

When instructed to build a feature:
1. Use your Atlassian tools to read the feature instructions from Jira
2. Develop the feature - do not skip any step from the feature-dev 7 step process
3. Thoroughly test the feature with unit tests and integration tests and fix any issues
4. Submit a PR using your github tools

## AI Desing

When writing code to make calls to LLMs, use your Cerebras skill to use LiteLLM via OpenRoute to the gpt-oss-120b model with Cerebras as the inference provider. You should use Structured outputs so that you can interpret thre results and do what you have to do

There is an OPENROUTER_API_KEY in the .env file in the project root

## Technical design

The entire project is packaged with Docker Compose (2 services: `backend`, `frontend`)  
The backend is in `backend/` and is a uv project, using FastAPI  
The frontend is in `frontend/`, built with React + Vite + TypeScript  
Document every step needed to run and stop the project locally
There are scripts in scripts/ for:

```
scripts/start-linux.sh   # docker compose up --build -d
scripts/stop-linux.sh    # docker compose down
```

### Database

Backend uses SQLite as a "temporary database" — no separate DB container. On startup,
if the DB is empty, it's seeded from CSVs committed at `backend/seed_data/` (copied from
the prototype's `app/data/cinturao/games.csv` and `app/data/teams/teams.csv`). Seeding is
idempotent. Tables use proper `id` primary keys / foreign keys (the prototype joined
`teams`/`games` by exact name string match, which is fragile — don't repeat that).

Data is **not** re-scraped live for this foundation work — `src/scrapping/*` hits a live
third-party site (salaooval.com.br) via Selenium and is slow/fragile; re-running it is
out of scope unless a future ticket specifically asks for it.

### Old prototype (`app/`)

The Streamlit prototype in `app/` stays in place as a working reference — it is not
deleted when `backend/`/`frontend/` are added. Its view/UX is a guide, not a spec to
match exactly (see Overview above). It can be removed in a future ticket once the new
app reaches parity.

### Pages / scope

Foundation pages (ported from the prototype, not copied 1:1): Home (current champion),
Rules (static content, no backend round-trip needed), Games (sortable table with team
logos). The Stats/visualizations page is intentionally **mocked only** for this ticket —
static layout + one hardcoded example chart, not wired to real backend data or endpoints.
Do not build real stats/visualization endpoints until a ticket explicitly asks for them.

### Testing

Backend: pytest, with real unit/integration tests (seeding logic, routers via
`TestClient`, derived-stat logic like "current champion"), per the global "run tests
after making changes" preference.  
Frontend: minimal Vitest + React Testing Library smoke tests — not full coverage, just
enough to catch obvious breakage in a foundation-stage app.

## Color Scheme
- Accent Yellow: #ecad0a
- Blue Primary: #209dd7
- Purple Secondary: #753991 (submit buttons or something simillar)
- Dark Navy: #032147 (headings)
- Gray Text: #888888

