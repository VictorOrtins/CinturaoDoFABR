# Cinturão do FABR Project

## Overview

This is a Visualization-based app primarely focused on showing results and Basic/Advanced Stats about FABR, Futebol Americano Brasileiro. The idea is to fully showcase Cinturão do FABR, which is basically The Unofficial Football World Championships but for American Football in Brazil

There's already an app implemented at app/ folder where there's an UI with some data in app/data/ that already showcases what I roughly want. This was an early prototipe, before Claude, done with mostly Streamlit, and limited because of it aswell. You should use this as a guide, but you don't need to really follow what's inside of it because it has mostly a different view from what I want from this new website

**Before any frontend/visual work** (new pages, layout, typography, adding UI), read
[`docs/DESIGN.md`](docs/DESIGN.md) — it documents what makes fabrnetwork.com.br and
coparadiso.com feel distinctive (the two reference sites for this app's target look)
and concrete directions for closing the gap from the current, more generic "data tool"
look. Keep it updated when a session makes a deliberate design decision worth
remembering for the next one.

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

The backend Dockerfile runs as a non-root `appuser` (fixed UID 1000, matching the default
on most single-user Linux dev machines) so the SQLite file isn't root-owned on write.
The SQLite DB is stored in a **named Docker volume** (`backend_data`), not a host bind
mount — bind-mounting `./backend/data` breaks for the non-root container user, because
Docker creates missing bind-mount source directories as root on the host, which the
non-root container user then can't write into. A named volume avoids this: Docker
initializes it from the image's `/app/data` (already `chown`'d to `appuser` in the
Dockerfile), so permissions are correct from the start.

**Gotcha**: if the Docker Compose stack is already up (`scripts/start-linux.sh`), it
occupies host ports 5173 and 8000. Running `uv run uvicorn`/`npm run dev` directly for
manual verification alongside it will silently bind to a fallback port (or fail) instead
of the one you asked for — always confirm the actual bound port from the process's own
log output rather than assuming. The dev backend also needs
`BACKEND_CORS_ORIGINS='["http://localhost:<dev-frontend-port>"]'` set, since the default
only allows `:5173`. Don't stop the Compose stack to free the ports — it may be the
user's own running environment; use different ports instead.

**Gotcha**: a manually-started `uv run uvicorn` (no `--reload`) does not pick up backend
code changes — it keeps serving whatever was loaded at process start. If a backend
change "isn't working" when checked live, confirm the server was actually restarted
after the edit before debugging the code itself; a stale process is a more likely
culprit than it seems.

### Database

Backend uses SQLite as a "temporary database" — no separate DB container. On startup,
if the DB is empty, it's seeded from CSVs committed at `backend/seed_data/` (copied from
the prototype's `app/data/cinturao/games.csv` and `app/data/teams/teams.csv`). Seeding is
idempotent. Tables use proper `id` primary keys / foreign keys (the prototype joined
`teams`/`games` by exact name string match, which is fragile — don't repeat that).

Data is **not** re-scraped live for this foundation work — `src/scrapping/*` hits a live
third-party site (salaooval.com.br) via Selenium and is slow/fragile; re-running it is
out of scope unless a future ticket specifically asks for it.

**Known data-quality gap**: `backend/seed_data/games.csv` and `teams.csv` have some
team-name mismatches (e.g. `"Juventude FA"` in games.csv vs `"União da Serra/Juventude FA"`
in teams.csv). `src/preprocessing/*.py` has partial alias fixes for some of these that were
never applied to these committed CSVs. `backend/app/seed.py::_seed_games` skips any game
where either team name doesn't resolve exactly (case-sensitive), logging a warning rather
than guessing at fuzzy matches (which risks attributing a game to the wrong team). This
currently drops 20 of 165 games (145 seeded) — locked in by a regression test in
`backend/tests/test_seed.py` so future CSV changes are caught instead of silently drifting.
Reconciling the two CSVs properly (using `src/preprocessing`'s alias dicts as a starting
point) is a good follow-up ticket, not done here.

### Old prototype (`app/`)

The Streamlit prototype in `app/` stays in place as a working reference — it is not
deleted when `backend/`/`frontend/` are added. Its view/UX is a guide, not a spec to
match exactly (see Overview above). It can be removed in a future ticket once the new
app reaches parity.

### Pages / scope

Foundation pages (ported from the prototype, not copied 1:1): Home (current champion),
Rules (static content, no backend round-trip needed), Games (sortable table with team
logos). The Stats/visualizations page (CDF-2) is real and wired to live backend data —
a `<select>` picks one of 12 visualizations, rendered via a discriminated-union
`StatDefinition` in `frontend/src/pages/StatsPage.tsx` (`kind: "leaderboard" | "timeline"
| "region" | "trend" | "histogram"`, each with its own chart component). Not every stat
is a horizontal bar chart — see "Stats/visualizations architecture" below before assuming
a new stat should be.

Team pages (`/times` list, `/times/:id` detail — `frontend/src/pages/TeamsPage.tsx` /
`TeamDetailPage.tsx`) exist: a hero banner using the team's own `primary_color`, a
white "logo plate" behind the badge (needed — several team logos are the same hue as
their own brand color and are invisible without a neutral backing), a bio-card `<dl>`
for city/state/region/profile link, and the team's last 5 title games with a win/loss
badge. **`/times` only lists teams that have actually played a title game** — see
"Teams vs. games participants" below; don't switch it back to the unfiltered
`/api/teams` response.

### Backend API (implemented so far)

- `GET /health`
- `GET /api/teams` (add `?played=true` to get only teams that appear in a game — see
  below), `GET /api/teams/{id}`, `GET /api/teams/{id}/games` (that team's games,
  chronological, 404s if the team doesn't exist)
- `GET /api/games` (team info embedded, mirrors the prototype's `jogos.py` table shape)
- `GET /api/cinturao/current` (current champion + `champion_since`, the date their
  current unbroken reign started — computed in `backend/app/services/cinturao.py` by
  walking games chronologically and resetting on every winner change)
- `GET /api/stats/*` (CDF-2, `backend/app/routers/stats.py` +
  `backend/app/services/stats.py`) — one endpoint per visualization:
  `title-defenses`, `title-wins`, `most-games`, `most-losses`, `title-losses`,
  `days-with-title`, `longest-reign`, `longest-win-streak` (all `list[LeaderboardEntry]`,
  team + value, top 10), plus `reign-timeline`, `titles-by-region`, `games-per-year`,
  `score-margin-distribution` (each its own response shape — see service module for the
  dataclasses). Check here before adding a new stats endpoint that might already exist.
- `POST /api/assistant/query` (CDF-3, `backend/app/routers/assistant.py`) — natural-language
  chat that generates *new* visualizations on demand, additive to the hardcoded `/api/stats/*`
  set above (never replaces it). See "AI assistant / natural-language queries (CDF-3)" below.

### Teams vs. games participants

`backend/seed_data/teams.csv` is a broad FABR team directory (182 rows) — most of those
teams never held or contested the belt. Only ~49 teams actually appear as a
home/away side in `games` (which, per "Stats/visualizations architecture" below, only
ever contains title matches). Any UI or query framed as "teams in the Cinturão"
(the `/times` page, anything similar added later) must filter by game participation —
`teams_service.list_teams(db, played_only=True)` does this by computing the set of
`home_team_id`/`away_team_id` values in Python (not a SQL join; dataset is small enough
that a plain-Python set is simpler and matches this codebase's existing style). Don't
assume `GET /api/teams`'s default (unfiltered) response represents "who has played."

### Stats/visualizations architecture (CDF-2)

The `games` table only ever contains **title/belt matches** (seeded from the
prototype's already-belt-computed `cinturao/games.csv`), and every such game has
`winner_team_id` set (never null) — `defender_team_id` is null only for game 0 (no prior
holder). This means **the belt-succession algorithm
(`src/cinturao_algorithm/cinturao.py`) does not need to be reimplemented for stats** —
`winner_team_id`/`defender_team_id` are already correct per game; new stats are plain
aggregations over that, following `get_current_champion`'s style (load games ordered
chronologically, walk them in a plain Python loop, no ORM aggregate queries).

`backend/app/services/stats.py`'s `_reign_periods()` (a list of `ReignPeriod(team_id,
start, end, ongoing)`) is the shared primitive behind three stats: `get_days_with_title`
(sum durations per team), `get_longest_reign` (max duration per team), and
`get_reign_timeline` (the periods themselves, for the Gantt-style timeline chart). It
takes an optional `now` param specifically so tests can freeze "today" instead of
depending on wall-clock time.

Porting the old Streamlit stats page (`app/pages/stats.py` /
`app/utils/visualization_utils.py`) surfaced two real bugs, fixed rather than carried
over: a stat labeled "most consecutive title games" was wired to the wrong function
(duplicated `get_most_cinturao_defenses` instead of the actual streak-counting
function) — now `get_longest_win_streak`; and the "consecutive days with title" stat
used a **hardcoded date** (`2025-01-25`) instead of `datetime.now()` for the ongoing
reign — now always computed live (or from the injectable `now` param in tests).

Frontend chart components (`frontend/src/components/`): `LeaderboardChart` (horizontal
bars, colored per-team via `primary_color`), `ReignTimelineChart` (Gantt-style: two
stacked `Bar`s per row — a transparent offset + a colored duration — X axis is days
since the first reign, `MIN_VISIBLE_DAYS` floors very short reigns to a still-hoverable
width), `TitlesByRegionChart` (a single stacked bar, **not a pie** — the dataviz skill
flags pie/donut for part-to-whole comparisons; regions aren't teams so they use the
dataviz skill's validated 5-slot categorical palette, checked with
`scripts/validate_palette.js` against this app's actual light/dark chart surfaces, not
eyeballed), `GamesPerYearChart` (line/area), `ScoreMarginHistogram` (vertical bars).
Shared tooltip styling lives in `frontend/src/components/chartTheme.ts`.

`StatsPage.tsx`'s data-fetching effect guards against out-of-order responses (a
cancellation flag set in the effect cleanup) — rapid `<select>` changes fire overlapping
requests, and without the guard a slower stale response can overwrite the currently
selected stat's data. This is a real risk here (unlike `GamesPage`/`HomePage`, which
only fetch once on mount) because switching stats re-fetches on every change.

### AI assistant / natural-language queries (CDF-3)

Unlike CDF-2's fixed 12-stat menu, CDF-3 lets a user ask for a visualization that
doesn't exist as a hardcoded endpoint (e.g. "title defenses by region", "games per year
for teams from RS") without hardcoding a new stat function per question. It's a new
page/route (`/assistente`), strictly additive — it never touches `/api/stats/*` or
`StatsPage.tsx`.

The LLM never generates SQL or touches team IDs/colors directly — it only fills in a
constrained, validated spec (`backend/app/services/query_engine.py`) built around a
generic **`FieldRef`** (`{entity: "team"|"game", column: str, transform: str}`), reused
everywhere a "which piece of data" question comes up: `group_by`, `sort_by`, and each
filter's `field`. `column` is validated against a per-entity whitelist (`team`:
name/region/state/home_city; `game`: date/venue/tournament/phase/home_score/away_score
— color/logos excluded, no color vocabulary exists) and `transform` against what's legal
for that column's kind (`identity` always; `initial` for text columns; `year`/`decade`/
`month` for the date column only).

`team_role` (home/away/participant/winner/defender/loser) stays a closed enum — a game
only has these structurally fixed roles. Required whenever any `FieldRef` in the spec is
`entity="team"`, except with `metric_field="teams"` (below). `metric_field`/
`aggregation` also stay closed enums (exhaustive list of measurable things in this
schema).

**`metric_field="teams"` counts distinct TEAMS, not games** — needed because the
games-loop below can't answer "which region/letter has the most teams" without a team
that played many title games outweighing one that played once. Separate code path
(`_execute_team_count`) over `teams_service.list_teams(db, played_only=True)`; requires
`group_by.entity == "team"`, forbids `team_role`/`outcome_filter`/game-entity filters,
only `aggregation="count"` — enforced by `QuerySpec`'s validator.

Everything else (`_execute_game_metric`) walks `ordered_games()` once as before,
resolving each game's subject team(s) per `team_role`, plain-loop bucket/aggregate — same
style as CDF-2. Still dedupes per `(game.id, bucket_key)` so a `PARTICIPANT`-role game
whose two teams land in the same bucket isn't double-counted
(`test_participant_does_not_double_count_*`).

`filters` is `list[FilterClause]` (`field: FieldRef`, `op: "equals"|"gte"|"lte"`,
`value: str`). `equals` on an untransformed text field fuzzy-matches via difflib
(`known_field_values()`, any whitelisted text column); `gte`/`lte` only valid for
date/numeric columns. A team-entity filter with no `team_role` set matches either the
home or away team.

`chart_type` is inferred from `group_by`'s shape: `team.name` untransformed →
`"leaderboard"`; date column as `year`/`decade` → `"line"`; else `"bar"`. `QuerySpec`/
`TableSpec` both have explicit `sort_by`/`direction` (defaults preserve prior behavior —
value-desc for leaderboards, key-asc/no-limit for timelines, chronological/alphabetical
for tables) — this is what fixed "últimos 5 jogos" always returning the earliest games
instead of the most recent.

**`team_role="participant"` vs `"home"` for region/year grouping is a real ambiguity,
not a bug**: a cross-region game genuinely touches two regions, so summing appearances
across regions can legitimately exceed the total game count (standard sports-stats
convention) — but it reads as "wrong" for a plain "how many games were played per
region" question. The system prompt in `llm_query.py` steers the model toward
`team_role="home"` for that phrasing (a game's host is a single, unambiguous value, so
totals sum to the real game count) and explicitly warns about `"participant"`'s
double-attribution risk. If this surfaces again, it's a prompt-tuning problem, not an
engine bug — the engine's participant math was independently verified correct.

**A "no games found" answer isn't always a bug** — no Nordeste team has ever been a
title *defender* (as opposed to challenger), so "defesas de título na Região Nordeste"
legitimately returns empty. Verified against the seeded DB, not assumed; see
`test_defender_role_with_region_filter_returns_empty_when_no_team_defended`.

`backend/app/services/llm_query.py` builds the prompt (grounded with live team
names/regions/states/tournaments/venues/phases via `known_field_values()`, so the model
can't invent values that don't exist) and calls `litellm.completion` per the Cerebras
skill (`.claude/skills/cerebras/SKILL.md`), requesting `response_format=
LLMQueryResponse` — `status: "ok"|"unsupported"` so the model can decline instead of
hallucinating. `output: "chart"|"table"` picks `spec: QuerySpec` vs `table: TableSpec`
(`entity: "games"|"teams"` + the same `list[FilterClause]`).
`query_engine.execute_table()` reuses `_resolve_clause`/`_clause_passes` from the chart
path but returns plain `TableResult(columns, rows)` — no aggregation, no chart-type
inference.

`backend/app/services/assistant.py` orchestrates `llm_query.interpret` →
`query_engine.execute`/`execute_table` into an `AssistantAnswer(status: "ok" |
"unsupported" | "error", message, output: "chart" | "table", chart, table)` — three
status funnels only, never a 500 for a "bad" question. The response is chart/table +
deterministic server-built label only, no LLM-authored caption sentence (kept to one LLM
call per question).

`OPENROUTER_API_KEY` is read from the repo-root `.env` via `backend/app/config.py`'s
`env_file` (added for this feature — `Settings` previously only read `BACKEND_`-prefixed
process env vars) using a `validation_alias` that deliberately bypasses the `BACKEND_`
prefix convention, to match the key's existing unprefixed name in `.env`.
`docker-compose.yml`'s `backend` service needed `env_file: .env` added too, since it
previously didn't forward the root `.env` into the container at all.

Frontend: `AssistantPage.tsx` branches on `AssistantAnswer.output` first —
`"table"` renders `AssistantTable.tsx` (a plain `<table>` over `columns`/`rows: Record<
string,string>[]`, no chart at all); `"chart"` falls into the existing dispatch below.
`chart_type` (`leaderboard` | `bar` | `line`) is decided server-side from
`group_by`, never guessed client-side. `AssistantChartAnswer.tsx` dispatches on it,
reusing the *existing* `LeaderboardChart` unmodified for `leaderboard` (real `Team`
objects with `primary_color`, same as CDF-2). `bar`/`line` render through
`LabeledBarChart`/`LabeledAreaChart` (`frontend/src/components/`) — generic
presentational shells (generic on a `T`, parameterized by `xKey`) shared with
`ScoreMarginHistogram`/`GamesPerYearChart`, which were refactored into thin wrappers
around them rather than duplicating the recharts JSX a third/fourth time.
`AssistantPage.tsx` is single-shot (no conversation memory/history) — each submit
replaces the previous answer.

### Testing

Backend: pytest, with real unit/integration tests (seeding logic, routers via
`TestClient`, derived-stat logic like "current champion"), per the global "run tests
after making changes" preference.
Frontend: minimal Vitest + React Testing Library smoke tests — not full coverage, just
enough to catch obvious breakage in a foundation-stage app.

**Gotcha**: the in-memory SQLite engine used by backend tests (`make_engine(":memory:")`
in `backend/app/database.py`) must use `poolclass=StaticPool`. Without it, FastAPI's
`TestClient` runs requests on a different thread than the test fixture, and SQLite's
default `:memory:` behavior gives each thread its own separate empty database — tables
created by the fixture become invisible to the route handlers, failing with
`no such table`. `StaticPool` keeps a single shared connection alive across threads.

For endpoints that only differ by URL (the 8 `/api/stats/*` leaderboard routes), a single
`@pytest.mark.parametrize` test over the path list (`test_routers.py`) is preferred over
one near-identical test function per route.

**Gotcha**: recharts' `<ResponsiveContainer>` sizes itself via `ResizeObserver` +
`getBoundingClientRect`, neither of which jsdom implements with real layout — without a
polyfill it stays at 0×0 and no chart children (axes, bars) ever mount. The polyfill
lives once, globally, in `frontend/src/test/setup.ts` (not per-test-file). Even with it,
jsdom still can't do real text measurement, so recharts' categorical axis tick *labels*
and zero-value bars often don't render — don't assert on rendered axis text or an exact
bar count when a bucket can be zero; assert on structural counts instead (e.g.
`container.querySelectorAll(".recharts-bar-rectangle")`, see
`frontend/src/test/LeaderboardChart.test.tsx`).

### Frontend tooling notes

- `react-router-dom` is pinned to `^7.18.2` (not left on a lower 7.x). `npm audit` flags
  most of the 7.x line for an "RSC Mode CSRF Bypass" advisory — this app is a plain SPA
  (`BrowserRouter`, no React Server Components/server actions), so the advisory doesn't
  apply, but staying on the latest patch avoids a long list of *other*, more serious
  advisories (open redirect/XSS/RCE) that affect versions below ~7.17.
- `backend/pyproject.toml`'s `[tool.ruff.lint] select` is scoped to `["E", "F", "I", "UP"]`
  rather than ruff's fuller rule set. Ruff's default install otherwise also flags `B008`
  (FastAPI's idiomatic `Depends(get_db)` in argument defaults — a false positive here) and
  `DTZ00x` (naive datetimes — game dates are intentionally naive local timestamps, matching
  the source CSVs). Keep this scoped selection rather than re-enabling those.
- **Never set `display: flex` (or `grid`) directly on a `<td>`.** It breaks the table
  layout algorithm — the browser stops sizing/aligning that cell as a real table-cell,
  which showed up as visibly uneven row heights across a `<tr>` and one column
  (`GamesTable`'s "Defensor do Cinturão") rendering as if empty. If a cell's content
  needs its own flex row (icon + text), put the flex styling on an element *inside* the
  `<td>` (see `.games-table__team-link` in `GamesTable.css`) and leave the cell itself
  as a normal table-cell.
- To center an element between two unevenly-sized siblings (e.g. `Topbar`'s nav
  between the brand and the theme toggle), use a `1fr auto 1fr` grid with the element
  in the middle column, not flexbox + `margin-left: auto` on the trailing sibling —
  the flex version centers in the *leftover space*, which drifts off the bar's true
  midpoint whenever the two side elements aren't the same width.
- When a "nested" list/element reuses its parent's class for shared resets (e.g.
  `RulesPage`'s sub-rule `<ol>` was originally `class="rules-list rules-list--nested"`),
  a `.rules-list--nested > li::before` override rule does **not** fully replace
  `.rules-list > li::before` — both selectors still match (same element, both classes),
  so CSS merges their declarations, and any property the override doesn't redeclare
  (there: `background-color`, `border-radius`, `width`, `height`) leaks through from the
  base rule. Fixed by giving the nested list its own non-overlapping class
  (`rules-list--nested` alone, with its own `list-style`/reset) instead of trying to
  override a shared one.

### Frontend design system (redesign pass)

Read [`docs/DESIGN.md`](docs/DESIGN.md) first for the *why*; this is just a map of the
*where*. Implemented pieces worth reusing rather than re-inventing:
- `BeltIcon` (`frontend/src/components/BeltIcon.tsx`) — the repeatable line-art motif;
  used in the topbar wordmark and inside `LoadingBelt.tsx` (the branded loading
  spinner used across Home/Stats/Teams instead of bare "Carregando..." text).
- `--font-mono` (`frontend/src/index.css`, backed by `IBM Plex Mono` — already loaded
  in `index.html`, previously unused) is the "label/meta" type register: bio-card
  labels, chip text, loading captions. Anton stays for headings, Manrope for body
  prose — don't blur the three roles.
- `.chip` utility class (`index.css`) for status/category pills — currently used for
  `GamesTable`'s tournament column.
- `getContrastingTextColor` (`frontend/src/utils/color.ts`) — cheap brightness
  heuristic (not full WCAG luminance) used to pick white-vs-dark text over an
  arbitrary team `primary_color` hero background.
- Nav is a top bar, not a sidebar: `Topbar.tsx`/`Topbar.css` (full-width, sticky,
  brand left / pill-style nav center / theme toggle right; wraps to a second row on
  mobile). Always dark regardless of light/dark mode — `--sidebar-*` tokens in
  `index.css` are its bg/text vars (kept that name since `LoadingBelt`'s ring and a
  few other bits still reference "sidebar" as the dark-surface concept, not because a
  sidebar still exists). The active nav pill's text uses `var(--sidebar-bg)`, not
  `var(--color-dark-navy)` — the latter flips to a light value in dark mode for
  heading contrast, which would break contrast on the always-dark topbar. Nav links
  are centered on the bar via a `1fr auto 1fr` grid on `.topbar__inner` (see the
  centering gotcha below).
- `RulesPage.tsx`/`.css` — rules are numbered (legitimately: it's a literal rulebook),
  rendered via CSS counters (`.rules-list`/`.rules-list--nested`) into circular Anton
  badges for top-level rules and lettered mono labels for sub-rules, with `Ex:` asides
  pulled into a bordered `.rules-page__example` callout instead of inline text. See
  the nested-class cascade gotcha below before copying this pattern elsewhere.

## Color Scheme

"Arena" palette (chosen 2026-08-07 over two other explored directions — a refined
version of the original navy/blue/purple set, and a turf-green "Campo" direction):
fight-night-poster mood, near-black ink, amber spotlight accent, crimson secondary,
warm parchment surfaces in light mode. Accent and secondary hues were saturated up
2026-08-20 as part of an 8-bit/arcade pass (see docs/DESIGN.md) — flat, cartridge-vivid
yellow/blue/red instead of the original dusty/muted tones; ink, gray, and the parchment
surfaces were left as-is since they already read as high-contrast "cabinet" black-on-
cream. Defined as CSS custom properties in `frontend/src/index.css` (`:root` for light,
`[data-theme="dark"]` for dark) — these hex values are the light-mode ones; see that
file for the dark-mode overrides.
- Accent Yellow (amber spotlight): #ffb703
- Blue Primary (arcade blue, secondary/links): #1a54c4
- Purple Secondary (arcade red, CTA/secondary-button role): #e2231a
- Dark Navy (ink, headings): #171310
- Gray Text: #7a7168
- Page background (parchment): #efe6d3
- Surface (card bg): #fbf7ec

Recharts chart components (`LabeledAreaChart`, `LabeledBarChart`) can't read CSS custom
properties for SVG `fill`/`stroke` props, so their per-theme axis/grid/line/bar colors
are hardcoded hex duplicates of these tokens rather than `var(...)` — if the palette
changes again, grep those two files (and `chartTheme.ts`'s `FALLBACK_TEAM_COLOR`, and
`utils/color.ts`'s `getContrastingTextColor` dark-text return, which is intentionally
left as a fixed near-black/white pair independent of the brand accent hues) along with
`index.css`. `TitlesByRegionChart`'s 5-slot region palette is deliberately independent
of the app's brand tokens (regions aren't teams) and wasn't touched.

