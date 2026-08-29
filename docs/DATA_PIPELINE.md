# Data pipeline: scrape → DB → deploy (handoff doc)

**Status**: Phase 0 done (2026-08-23). Phase 1 done (2026-08-24 through 2026-08-26) and
**committed** (`1ff2c4d`, confirmed 2026-08-27 — the "nothing committed yet" framing
that used to be here was stale). **Phase 1.5 (Airflow DAG) is done** (2026-08-27/28,
branch `create-data-pipeline`) — see that section below for the full writeup, including
a real environment mistake worth reading before touching any venv/pip setup on this
machine again. **Phase 2 (backend DB sync) is done** (2026-08-28, same branch) — see
that section below; verified with a real `docker build` + container boot against the
Compose volume, not just pytest. **Phase 3 (`.github/workflows/scrape-and-pr.yml`) is
done, validated with real `workflow_dispatch` runs** (2026-08-29) — three real bugs
found and fixed (chromedriver version, headless Chrome, repo PR permission), plus two
real team-data merge decisions; see that section below for the full writeup. **Phase 4
(deployment) is in progress, mid-pivot** (2026-08-29, branch `phase4-fly-deploy`) —
Fly.io was tried first, worked, but turned out to require a paid tier by default
(no free allowance anymore) and was torn down; now moving to Render (backend) +
Cloudflare Pages (frontend), both genuinely free. See "Pivot away from Fly.io" in that
section for the full story. Phase 5 not started. This is everything a future session
needs to pick this up cold.

## Why this exists

The frontend (React/FastAPI/SQLite) is done and polished, but the user considers it
"pretty mid" as a portfolio piece on its own. What they actually want this project to
demonstrate is **data engineering**: a real, recurring pipeline that scrapes new FABR
match results, updates a database, and updates the live site — automated, and
visible as a pipeline (DAGs, PRs, deploys), not just a pretty page. This doc is the
result of a planning session (2026-08-22) scoping that out. Read
[`../CLAUDE.MD`](../CLAUDE.MD) first for the project's general architecture/gotchas —
this doc only covers the new pipeline/orchestration/deployment work, not the existing
backend/frontend.

## Current state (confirmed by reading the code, not assumed)

**Scraping** (`src/scrapping/`) — a real, previously-iterated-on Selenium scraper
against `www.salaooval.com.br` (a WordPress site, no API — this is the only data
source for the whole project). `src/scrapping/scrape_games/get_urls.py`'s
`TournamentUrlsScrapper` crawls the tournaments listing page and returns **every**
historical tournament URL (~50+); `scrapper.py`'s `GamesScrapper` scrapes two
different page layouts the site uses across years. It's a one-shot **full historical
re-crawl** today, not incremental, and there's no "only get new stuff" mode.

**Preprocessing** (`src/preprocessing/`) — cleans raw scraped CSVs: fixes hardcoded
team-name aliases, splits score strings, dedupes, computes the winner column.

**Belt algorithm** (`src/cinturao_algorithm/cinturao.py`) — walks the full
preprocessed, chronologically-sorted dataset from game 0 and recomputes the entire
belt-succession history every time it runs. This is cheap (pandas over ~165 rows) and
**needs no incremental logic of its own** — feed it the full merged dataset each run
and it's correct.

**Database** (`backend/app/seed.py::seed_if_empty`) — only ever fires once, against a
completely empty SQLite DB, from static CSVs committed at `backend/seed_data/`.
**There is currently no mechanism to update an already-seeded DB.** Team-name
resolution failures are silently dropped (`continue`), currently losing 20 of 165
games — documented as a known gap in `CLAUDE.MD`'s Database section.

**No CI/CD, no scheduler, no deployment** exist anywhere in the repo — the site only
runs locally via `docker-compose`/`scripts/start-linux.sh`. All of this is new work.

### Two real bugs found during research (fixed in Phase 0 / still open)

1. **Alias dicts disagree with each other.** ~~`src/preprocessing/games/preprocessor.py`
   renames `'Juventude FA'` → `'União da Serræ/Juventude FA'` (stray `æ` typo), while
   `src/preprocessing/teams/preprocessor.py`'s fix produces `'União da Serra/Juventude
   FA'`.~~ **Fixed in Phase 0**: consolidated into `src/utils/team_aliases.py`'s
   `TEAM_NAME_ALIASES`, typo corrected, both preprocessors now import and apply the
   same dict (verified: both `'Juventude FA'` and `'União da Serra'` now resolve to the
   identical `'União da Serra/Juventude FA'`).
2. **No raw/master dataset is committed anywhere.** `backend/seed_data/*.csv` is
   already-processed output (post-preprocessing, post-belt-algorithm), not raw scrape
   data. An incremental pipeline needs a durable, versioned place to merge new scrape
   rows into — this doesn't exist yet and has to be created (see Phase 1 below). Still
   open — Phase 1 work.

## Decisions confirmed this session (do not re-litigate without new user input)

1. **Deploy target**: Fly.io, for both `backend` and `frontend` — chosen for its
   persistent-volume support (needed for the SQLite file) and free allowance. Not
   deployed anywhere today.
2. **Scrape scope per run**: incremental — only current/recent-season tournaments,
   merged into a growing master dataset. Not a full re-crawl every time.
3. **Update flow**: a scheduled run opens a **PR** with the regenerated data for
   human review. It never auto-commits to `main` or writes to production directly.
4. **Orchestration/scheduling — the Airflow question**: the user wants real Airflow
   experience (DAG authoring, task dependencies, retries — genuinely more
   résumé-relevant than "a cron trigger in a YAML file") but **cannot pay for
   always-on infrastructure**, and running infra isn't the point of this project. The
   resolved approach (see below): **Airflow DAGs, executed ephemerally inside a free
   GitHub Actions runner** — real Airflow code, zero hosting cost. No persistent
   Airflow scheduler/webserver/metadata Postgres anywhere.
5. Consequence of #3: the live DB only updates when the backend **redeploys** (which
   only happens after the user merges the data PR to `main`), and it re-syncs itself
   from the committed CSVs on startup. CI never holds production DB credentials.

## The Airflow decision, explained

**Why plain Airflow-as-a-service doesn't fit**: Airflow's value is orchestrating many
interdependent tasks with retries/backfills/sensors across a complex DAG. This
pipeline is one linear chain (scrape → merge/dedupe → preprocess → belt algorithm →
sync DB) run once a week. Running Airflow "for real" means keeping a scheduler +
webserver + metadata Postgres alive 24/7 just to fire one job a week — that's real
infrastructure to host and pay for (self-hosted on Fly.io: a persistent machine
burning through the free allowance around the clock, plus a Postgres volume; managed
options like Astronomer/MWAA cost real money past a free trial).

**The free-tier-compatible middle ground**: Airflow ships a command specifically for
this situation — `airflow dags test <dag_id> <logical_date>` runs a DAG's tasks
locally, in dependency order, **without needing the scheduler daemon, webserver, or a
persistent metadata DB running**. It's Airflow's own recommended way to run a DAG
once, e.g. from CI. So the plan is:

- Write a real Airflow DAG (`dags/update_games_dag.py`) with `PythonOperator` tasks
  wrapping each pipeline step, real `>>` dependencies, and retry policies on the
  network-flaky scrape task — actual Airflow code, not a shell script.
- A GitHub Actions cron workflow installs `apache-airflow` fresh in the (free) runner,
  points `AIRFLOW_HOME` at a throwaway directory (SQLite metadata DB is fine — single
  run, no concurrency), runs `airflow dags test update_games <date>` once, then the
  runner is torn down. Zero persistent cost, ever.
- Trade-off, stated plainly: no persistent Airflow **web UI** to browse historical run
  history in a browser (you'd read GH Actions logs instead, or run `airflow standalone`
  locally on your own machine on demand if you want the UI experience for a demo/
  screenshot). No Airflow-driven scheduling either — recurrence still comes from GH
  Actions' `cron:` trigger; Airflow is the *execution engine* for one run, not the
  long-running scheduler. If that gap ever matters (e.g. you want a live dashboard to
  show off, or need real backfill/sensor features), self-hosting Airflow on Fly.io
  becomes a real upgrade path — see "Future upgrade path" below — but isn't needed to
  get genuine DAG-authoring experience now.

**A real risk to verify early, not assumed away**: Airflow's dependency tree is heavy
and version-sensitive (it publishes constraints files per Python version, e.g.
`pip install "apache-airflow==2.9.3" --constraint ".../constraints-3.12.txt"`). It may
pull in its own pinned `pandas`/other versions that conflict with what
`requirements.txt` already pins for `src/preprocessing`. **First thing to check when
implementation starts**: does `pip install apache-airflow==<pinned> --constraint ...`
alongside the existing `requirements.txt` deps resolve cleanly in a scratch venv? If
not, isolate Airflow's install (e.g. a separate venv/step in the CI job that only
Airflow's process uses, importing `src.pipeline.tasks` as an installed package) rather
than fighting the constraint solver.

## Build order

Ship in phases; each is independently useful and testable before moving to the next.

### Phase 0 — Groundwork (dependencies, packaging, alias fix) — **DONE (2026-08-23)**
- `requirements.txt`: added `selenium==4.27.1`, `webdriver-manager==4.0.2`,
  `requests==2.32.3`, and `lxml==5.3.0` (the last one wasn't in the original plan —
  `pd.read_html`, used by `GamesScrapper.__get_table_df`, silently needs `lxml` as an
  optional pandas dependency; without it every tournament using the homeaway-table
  layout raises `ImportError` at scrape time. Found by actually running the test suite,
  not by reading the code.).
- Added `__init__.py` under every `src/` subpackage; switched every relative/
  `sys.path`-hack import to absolute `src.x.y` form (`scrape_games.py`, both
  `scrapper.py` files, both `preprocess_games.py`/`preprocess_teams.py`,
  `tests/scrapper_test.py`). Convention going forward: invoke everything as
  `python -m src.<path>` from the repo root, or just `pytest`/`python -c` from repo
  root — both resolve `src.*` imports with no `sys.path` hacks needed.
- New `src/utils/team_aliases.py`: one `TEAM_NAME_ALIASES: dict[str, str]`
  consolidating (and fixing the `Serræ`→`Serra` typo in) the two previously-divergent
  alias dicts. Both `src/preprocessing/games/preprocessor.py` and
  `src/preprocessing/teams/preprocessor.py` now do
  `<column>.replace(TEAM_NAME_ALIASES)` (pandas' exact-value dict replace) instead of
  their own hardcoded per-name branches/`str.replace` substring calls.
- **Verify — ran `tests/scrapper_test.py` instead of a full historical re-crawl**
  (the doc's original plan): a full 50+-tournament crawl is slow and largely redundant
  with the existing per-tournament-layout test suite, which the user separately asked
  to have re-run after ~2 years untouched, as a real-world check that
  `salaooval.com.br` hadn't changed layout. Result: **12/13 passed on first real run**
  (after fixing the `lxml` gap above) — the scraper itself needed no code changes.
  The one failure (`test_mineiro_2012`) turned out to be a third real name-alias gap,
  not a scraper bug or a site layout change: `salaooval.com.br` has always shown two
  different labels for this team — the team's own bio-page `<h1>`/`<title>` says
  "América Locomotiva" (matches `backend/seed_data/teams.csv`'s existing row), while
  every game-listing table (SportsPress plugin's short competitor label, confirmed via
  raw HTML on the *same* 2012 tournament page) has always said "Locomotiva FA" — the
  exact same "short schedule-table label vs. full bio-page name" pattern as the
  pre-existing `Galo FA`/`Fluminense Imperadores`/`Joinville Gladiators` aliases, just
  not one anyone had scraped/noticed before now. Per user direction, canonicalized to
  **"Locomotiva FA"** (not the bio-page name): added `"América Locomotiva": "Locomotiva
  FA"` to `TEAM_NAME_ALIASES`, and — critically — renamed the already-committed
  `backend/seed_data/games.csv` (14 occurrences across `Mandante`/`Visitante`/
  `Vencedor`/`Defensor do Título`) and `teams.csv` (1 row) from "América Locomotiva" to
  "Locomotiva FA" too, since those files are seeded as-is (not reprocessed at seed
  time) and would otherwise have silently drifted from any future scrape output.
  Verified: `backend` test suite (90 tests) + `ruff` + `mypy` all still green after the
  rename; the test's hardcoded assertion was updated to match the scraper's raw output.
  Full `tests/scrapper_test.py` suite is green (13/13) as of this session. Conclusion:
  the scraper's *scraping logic* needs no changes for Phase 1, but this is a live
  example of exactly the failure mode the user was worried about (a name variant
  silently fragmenting a team's history) slipping past both the alias dicts *and* the
  already-committed seed data at the same time — worth a systematic pass (not done
  here) cross-checking every team's schedule-table label against `teams.csv`'s name
  before Phase 1 ships, rather than relying on catching each one via an incidental test
  failure.
- **Perf fix found via the same test run, not in the original plan**:
  `GamesScrapper.__scrape_tournament` visits every tab on a tournament page (e.g.
  "Informações"/"Campeões"/"Notícias", not just the actual games tab) and, per tab,
  waits up to `wait_time` (30s) each for a `.paginate_button` and for
  `time.sp-event-date` (cards) — elements that, per this profiling, either render
  near-instantly (server-side WordPress/SportsPress, no async loading observed across
  3 different tournaments/layouts) or genuinely don't exist for that tab's layout.
  Profiling `campeonato-mineiro-2012` (5 tabs, table-only, no pagination) showed 300 of
  its 312s total was pure timeout waiting on elements confirmed absent. Fixed by adding
  `GamesScrapper.optional_element_wait_time` (default 3s, vs. `wait_time`'s 30s) used
  only for those two "may not exist on this tab" probes — every other wait (initial tab
  list, per-row extraction once a card/table is confirmed present) is untouched, so no
  scrape correctness/coverage was traded for speed. Full 13-test suite: **44:33 → 12:11
  (3.65x), 13/13 still passing, identical row counts** — confirms nothing was lost.
  Not addressed (flagged, not fixed): the tab loop still fully reloads and re-scrapes
  the *same* page content once per irrelevant tab (confirmed for at least the
  table-only layout — all rows are present on a single page load, no anchor needed);
  deduping happens after the fact via `drop_duplicates`. Deeper fix would mean touching
  the tab-iteration logic itself, which risks silently dropping real per-tab
  differences on layouts not manually verified here (e.g. tournaments where different
  tabs genuinely hold different phases/games) — left alone this session.

### Phase 1 — Local incremental pipeline logic (orchestrator-agnostic)
Write this as plain, importable functions first — Airflow (Phase 1.5) just wraps them
in `PythonOperator`s later. Don't build DAG structure and pipeline logic in the same
step.

- `src/scrapping/scrape_games/get_urls.py`: add a pure, unit-testable
  `filter_urls_by_year(urls, since_year)`. Tournament URL slugs reliably end in a
  4-digit year (confirmed from existing code) — regex filter, no new scraping
  capability needed. Keep URLs with no recognizable trailing year rather than
  dropping them (never silently lose an edge case). Leave
  `TournamentUrlsScrapper.get_urls()` itself untouched.
- New `src/pipeline/tasks.py` — one function per pipeline step, each independently
  callable/testable:
  - `scrape_recent_games(since_year: int) -> Path` — builds the URL scraper, applies
    `filter_urls_by_year(since_year=current_year - 1)` (covers a season still being
    finalized), runs the existing `GamesScrapper` unchanged, writes to a **new,
    timestamped file** under `data/raw/games/` (never overwrites).
  - `merge_and_preprocess() -> Path` — `Preprocessor().read_data_in_folder('data/raw/games')`
    (reuses its existing "concat every file with 'games' in the name" behavior
    unmodified — concats the one-time bootstrap file plus every past incremental
    delta) → `preprocess_games_df()`. The existing dedupe key
    (`Data,Mandante,Hor/Res,Visitante,Torneio`) means an unchanged re-scraped game is
    a no-op; only genuinely new rows survive.
  - `run_cinturao(preprocessed_path: Path) -> Path` — `Cinturao(...).run_cinturao_algorithm()`,
    full recompute over the merged set, writes the result.
  - `regenerate_seed_csv(cinturao_output: Path) -> None` — overwrite
    `backend/seed_data/games.csv` with the result.
  - `check_unresolved_teams() -> Path` — diff team names appearing in the new
    games.csv against `backend/seed_data/teams.csv`; write any unresolved names to
    `data/raw/unresolved_teams.txt`. **Does not raise/fail** — surfaced for human
    review in the PR body instead (decision #3).
- New `src/pipeline/update_games.py` — thin CLI (`argparse`: `--since-year`,
  `--dry-run`) that calls the Phase 1 task functions in order, for local/manual runs
  without Airflow. Both the CLI and the future Airflow DAG import from
  `src/pipeline/tasks.py` — one implementation, two callers.
- New committed raw-data location: `data/raw/games/` — one one-time **bootstrap
  file** (produced by running the existing full historical scraper once locally and
  committing the output), plus one new file per scheduled run.
- `.gitignore`: currently blanket-ignores `*.csv` except a small allowlist whose
  `app/*` entries are now dead (`app/` was deleted). Replace them with
  `!data/raw/games/*.csv` (add `!data/raw/teams/*.csv` too if team scraping gets
  wired in later) so the pipeline's output can actually be committed.
- **Trust-building milestone before moving on**: run `update_games.py` against the
  bootstrap file alone (no new scrape) and confirm it reproduces the
  currently-committed `backend/seed_data/games.csv` (modulo the alias-typo fix).
- **Known limitation to flag, not fix now**: the dedupe key includes the score, so a
  *corrected* score on an already-scraped game would be treated as a new row rather
  than an update. Leave a comment near the dedupe call; changing `Preprocessor`'s key
  is out of scope here.

#### Phase 1 progress (2026-08-24) — interrupted mid-run, not done

**Built and working**: `filter_urls_by_year` (with unit tests covering trailing-year
present/absent/boundary cases), `src/pipeline/tasks.py` (all 5 task functions, each
taking optional path params so they're testable against tmp-dir fixtures rather than
real `data/`/`backend/seed_data/` paths), `src/pipeline/update_games.py` (the
`--since-year`/`--dry-run` CLI), `data/raw/games/` + `.gitignore` allowlist as planned.
Integration tests for `merge_and_preprocess` (dedupe + alias fix) and
`check_unresolved_teams` pass. A root `.venv` (via `uv`, `requirements.txt` + `pytest`)
was created for these scripts — nothing existed at repo root for this before. **None of
this is committed** — it's real, working tree state on `create-data-pipeline`.

**The trust-building milestone is not complete.** The plan was: run the existing full
historical scraper once (`add_fabr_game_day=True`, since that flag already exists
specifically for the un-scrapable first FABR game — no new code needed for that part),
then confirm `merge_and_preprocess` → `run_cinturao` reproduces
`backend/seed_data/games.csv`. Attempting this surfaced real, previously-unknown
scraper bugs — fixing them was necessary before the milestone could even be attempted
properly, and doing so ran the process long enough that the user stopped it mid-scrape
to end the session. **Do not assume the scraper needs no further changes** the way
Phase 0's verification concluded — that conclusion covered only the 13-tournament test
sample, not a real 208-tournament full crawl, and it doesn't hold at full scale.

**Real bugs found and fixed this session** (all in the working tree, none committed):
1. `TournamentUrlsScrapper` (`get_urls.py`) was rewritten from DOM-scraping the
   `/campeonatos/` listing page's body content to querying the WordPress REST API
   (`GET https://www.salaooval.com.br/wp-json/wp/v2/pages?parent=14`, paginated). The
   listing page had silently stopped being updated after 2024 — 2025/2026 tournaments,
   including the brand-new **Superliga** national championship, were completely
   invisible to the old scraper despite having real, scrapable game data. Every
   tournament page is a child of the same CMS parent page (id 14) regardless of
   category or year, so this has no staleness and needs no year-guessing — a new
   tournament shows up the moment it's published. This also made the old
   `__append_missing_urls` hand-patches (a typo'd `matogrossense` slug, a duplicated
   2018 link, a missing 2019 one) unnecessary; verified via the live REST response and
   dropped rather than carried over. Full detail + how this was diagnosed: see
   `get_urls.py`'s own comments and `tests/get_urls_test.py`.
2. `GamesScrapper.__scrape_tournament` (`scrapper.py`) now falls back to scraping the
   current page directly when `__find_tournament_tabs` finds no `vc_tta-tabs` wrapper
   at all, instead of skipping the tournament entirely. Newer tournament pages (e.g.
   `campeonato-pernambucano-2025`, `spfl-2026`) render the same games tables with no
   tab structure whatsoever — confirmed live, this recovered real games that were
   previously silently dropped. See `test_pernambucano_2025_sem_tabs`.
3. `__get_card_result` now skips (with a warning, not a crash) a card row where fewer
   than 2 `span.team-logo` elements are found, instead of raising `IndexError`. This is
   a genuine site content gap (one team's logo widget was never set for two matches in
   `sao-paulo-football-league-2022`), not a scrape-timing issue — confirmed via manual
   DOM inspection; the opponent's name only exists as loose, unstructured text in the
   match title, not resolvable to `teams.csv`'s naming.
4. **The big one**: `__scrape_current_tab` used to *only* call `__scrape_games` as a
   side effect of a successful pagination-button click — if a tab's pagination
   controls exist in the DOM but are non-interactable (`is_displayed() == False`,
   which happens whenever the underlying DataTable's data already fits on one page —
   confirmed for `campeonato-brasileiro-2012`/`-2013`,
   `campeonato-mato-grossense-2020`, `campeonato-catarinense-2020`), every click throws
   `ElementNotInteractableException`, which was silently swallowed, so `__scrape_games`
   was **never called at all** and the tab returned 0 rows despite the data already
   being fully visible on load. Fixed by always scraping current state first,
   unconditionally, then attempting to paginate for any additional pages. This is
   disproportionately important: the cinturão algorithm needs an *unbroken* chain of
   the champion's games, so losing even one tournament this way (in this case, exactly
   the one where Fluminense FA's 2011-12-10 title reign continues) collapsed the whole
   reconstructed history from 165 games down to ~35. Validated against
   `test_campeonato_brasileiro_2012` (expects exactly 108) — passed after the fix, but
   was non-deterministic once (106/108) across repeated runs, so this class of
   pagination flakiness isn't fully eliminated, just made far less damaging (page-1
   content is never lost anymore, even if a later page occasionally is).
5. **Not a bug, but tripped up debugging**: team-name aliasing (`TEAM_NAME_ALIASES`)
   happens in `Preprocessor`, not at scrape time — a raw scraped row uses the site's
   own raw label (e.g. `"Fluminense Imperadores"`), not the alias-resolved name (e.g.
   `"Fluminense FA"`). Searching raw/scraped data for an alias-resolved name will
   silently find nothing even when the row is present.
6. Superliga's newer table layout introduces extra raw columns (`Liga`, `Unnamed: 6`)
   not seen on older tournament pages, plus a couple of DataTables "No data available
   in table" placeholder rows getting scraped as if real. Checked: both are already
   handled correctly by existing preprocessing (`Liga` just rides along unused;
   `__remove_unplayed_matches` correctly drops the placeholder rows and future/
   unplayed Superliga 2026 fixtures via their unparseable score strings) — no fix
   needed, but worth knowing before assuming a new "column count" issue is a bug.

**The bootstrap script itself had a bug, separate from the scraper**: the throwaway
script used to run the full crawl (lived in a session scratchpad, not committed) called
`scrape_tournaments(..., add_fabr_game_day=True)` but never re-saved the returned
`all_games` to CSV afterward — `add_fabr_game_day` appends its row to `all_games` in
memory *after* the loop that calls the scraper's own incremental `__save_to_csv`, so
the FABR day game was silently missing from disk even though `len(all_games)` in memory
included it. **Anyone re-running a full bootstrap crawl must explicitly
`all_games.to_csv(path, index=False)` after `scrape_tournaments` returns** — don't
trust the scraper's own incremental saves to include it.

#### Phase 1 progress (2026-08-24, continued) — full bootstrap crawl complete, trust milestone diagnosed

**The interrupted crawl was resumed and completed this session, safely (by slug, not
index, per the plan below).** `data/raw/games/games_bootstrap_part2.csv` now holds the
remaining 178 tournaments (4172 rows, incl. the one-time FABR day game), scraped with
zero tracebacks/exceptions — only 3 known "missing team logo" data-gap warnings (the
already-documented site content gap, not a new issue). Combined with the original
`games_bootstrap.csv` (30 tournaments, 2070 rows), **all 208 live masculino tournament
URLs are now covered.** Two tournaments (`campeonato-mato-grossense-2020`,
`campeonato-catarinense-2020`) returned 0 games — verified via raw `curl` (no JS) that
their tables are genuinely empty in the site's own HTML, and no 2021 page exists for
either league at all; consistent with COVID-cancelled 2020/2021 seasons, not a scraper
bug (confirmed before trusting it, per this doc's own standing caution not to assume).

**Ran the actual trust-building milestone**: `update_games.py --dry-run` over the
completed bootstrap → compared the resulting `data/processed/games_cinturao.csv`
against the committed `backend/seed_data/games.csv`. Initial diff was large (148 vs 165
rows, 65 missing / 48 extra) — investigated rather than accepted or dismissed:

1. **Found and fixed a second real alias gap**, same class as the `América
   Locomotiva`/`Locomotiva FA` one from Phase 0: the site's raw schedule-table label for
   one team is split between `"T-Rex"` (146 raw occurrences) and `"Timbó Rex"` (34
   occurrences) across many years (2010-2024) — confirmed both exist in the raw scraped
   data for what's the same team. Unlike the Locomotiva case, here the **already-
   committed `teams.csv`** uses the long form (`Timbó Rex`, with site slug
   `/times/timbo-rex/`), so canonicalized the other direction: added `"T-Rex": "Timbó
   Rex"` to `TEAM_NAME_ALIASES` (not committed yet, working tree only). Re-running after
   this fix improved the diff to 180 vs 165 rows (16 missing / 31 extra) — a real, now-
   fixed bug, not chased away by tolerance.
2. **Traced why an exact reproduction isn't the right bar, and shouldn't be chased
   further**: confirmed via direct row inspection that `Cinturao.run_cinturao_algorithm`
   (`src/cinturao_algorithm/cinturao.py`) is a **linear greedy walk** — start at game 0,
   take its winner as champion, find that champion's chronologically-next game by name
   match, its winner becomes the new champion, repeat. This means **any single upstream
   correction (like the T-Rex fix) cascades and reshapes every downstream game in the
   chain from that point on** — a team's title-defense games were previously split
   across two name-identities, so fixing the split doesn't just add rows, it changes
   which game counts as "the champion's next game" from 2010/2011 onward, producing a
   legitimately different (and more correct) sequence, not a subset/superset of the old
   one. The remaining 16/31 diff is this expected fingerprint, not a new defect — verified
   by checking that the *raw* and *preprocessed* data for the affected games (e.g. JEC
   Gladiators' 2011 Campeonato Catarinense games) were present all along; an earlier
   manual check that seemed to show them missing was a case-sensitivity bug in the
   diagnostic query itself (`'campeonato-catarinense-2011'` vs. the preprocessor's own
   title-cased `'Campeonato Catarinense 2011'`), not a real gap — worth remembering
   before trusting a quick manual diff over the pipeline's own output.
3. **One relabeling traced to genuine site content drift, not a bug**: two games
   (2018-10-14, 2019-01-13) are tagged `Copa Ouro 2017` in the old committed data but
   `Copa Ouro 2018` in the new scrape — confirmed `copa-ouro-2018` is a real, separate
   live tournament page (10 games) distinct from `copa-ouro-2017` (27 games); the site's
   own tournament categorization for these two games evidently changed sometime after
   the old seed data was originally generated. Not fixable in our code — flagged as a
   real, if narrow, category of drift: **the source site's history isn't append-only**,
   it can silently reclassify old content.
4. **`check_unresolved_teams()` confirmed stable, not a new gap**: ran it against both
   the new and old outputs — the unresolved-name set (13 names each) is nearly
   identical; the only differences are two brand-new 2026 teams (`Calvary Cavaliers`,
   `Ponta Grossa Phantoms`, expected — new tournament, not yet in `teams.csv`) and two
   names the new run resolves that the old baseline didn't. This is the same
   already-known, already-scoped-for-Phase-2 gap (`CLAUDE.MD`'s "20 of 165 games
   silently dropped" note) — not something this session introduced or needs to fix.
5. **Minor cleanliness gap found, and fixed the same session**: `Liga` (8 real
   Superliga division/phase values, e.g. `"Superliga D1 - Playoffs"`) and `Unnamed: 6`
   (always empty) both leaked from the raw Superliga table layout all the way into
   `games_cinturao.csv`'s column set — the doc's Phase 0 note that they "ride along
   unused" was true for correctness but didn't anticipate them surviving into the final
   seed-CSV schema, which the old committed `games.csv` doesn't have. Fixed: new
   `Preprocessor.__drop_unused_columns` step drops both explicitly (distinct from
   `__remove_zero_column`/`__remove_temporada_column`, which also filter out *rows* —
   `Liga` has real values on genuine games, so only the column should go, not the
   rows). Verified: re-ran the dry-run after the fix, `games_cinturao.csv`'s 11 columns
   now match the old committed CSV's exactly, row count unchanged (180), both test
   suites (pipeline 11/11, backend 90/90) still green.

**User review of the diff (2026-08-24, same session)**: presented the row-level diff as
an artifact grouped into new/relabeled/cascade (see point 2's explanation above).
Victor spot-checked the JEC Gladiators portion of the cascade bucket by hand and
confirmed it's accurate — "spot on." Also separately noted, while reviewing, one
playoff game that appears correctly captured now and was likely missed by whatever
scraper version produced the original committed data because it lived on a different
tournament-page tab — consistent with the tab-handling fixes in `CLAUDE.MD`'s scraper
section, not a new gap. Victor was also unsure whether the *original* 2024 generation
of `games.csv` re-ran the full pipeline every time a scraper bug was fixed, or only
sometimes — worth keeping in mind as another reason the old file isn't a perfect
ground truth to reproduce exactly.

**State at end of session**: `TEAM_NAME_ALIASES` has the `T-Rex` fix applied, and
`Preprocessor` now drops `Liga`/`Unnamed: 6` — both in the working tree, uncommitted.
`backend/seed_data/games.csv` has **still not been overwritten** —
`regenerate_seed_csv` was not called against the real path this session, only tested
against a scratch tmp file. Nothing has been committed. Remaining open decision point
for next session: whether to do a broader systematic alias-split audit (every team's
raw schedule-table label cross-checked against `teams.csv`) before treating name
resolution as trustworthy in general — two real splits (Locomotiva, T-Rex) have now
been found, both incidentally rather than systematically. The "is 16/31 an acceptable
trust bar" question from earlier this session is effectively resolved: Victor's manual
review confirmed the explanation holds up, so the actual next step is running
`regenerate_seed_csv` for real and deciding what to commit — not further diagnosis.

**Exact interruption state (2026-08-24), for resuming safely**: the last full crawl
attempt (208 masculino tournament URLs, via the new REST-based discovery) was killed by
the user 30 tournaments in. `data/raw/games/games_bootstrap.csv` on disk right now holds
those 30 tournaments' games (2070 rows) — index order is date-descending, most recent
tournament first (`superliga-2026` was tournament 0). **Do not resume by hardcoding a
URL-list index** — if a new tournament page gets published on the site before the next
session, the whole list shifts and an index-based resume would silently skip or
re-scrape the wrong tournaments. Instead, resume by slug: re-fetch the current URL list
via `TournamentUrlsScrapper(...).get_urls()`, filter out any URL whose slug already
appears in `games_bootstrap.csv`'s `Torneio` column (read the file's existing
`Torneio.unique()` for the exact list — as of this session it's the 30 tournaments from
`superliga-2026` through `campeonato-gaucho-2023`), scrape the remainder into a
*separate* new raw file, and add the FABR day game once (to either file — an exact
duplicate is harmless, `merge_and_preprocess`'s dedupe key would just collapse it if
added twice). `merge_and_preprocess` already concatenates every file with `games` in
its name under `data/raw/games/`, so a second partial file merges automatically — no
manual stitching needed. Once the crawl completes, re-run the trust-building comparison
against `backend/seed_data/games.csv` (the doc's original Phase 1 plan) before touching
`regenerate_seed_csv`/committing anything.

*(The crawl referenced above did complete later that session — see "Phase 1 progress
(2026-08-24, continued)" earlier in this doc. The "broader systematic alias-split
audit" it left as an open question is the subject of the next section.)*

### Team name slug audit (2026-08-26)

**Why**: as of 2026-08-24, two team-name splits (Locomotiva FA/América Locomotiva,
T-Rex/Timbó Rex) had been found - both incidentally, one via a test failure and one via
a manual diff review, not systematically. The open question left at the end of that
session was whether a third, unfound split could be silently fragmenting the belt
algorithm's chain-walking the same way T-Rex/Timbó Rex did (that one bug alone
collapsed 165 reconstructed games down to ~35 before it was caught). This section is
that systematic pass.

**Method**: a team's raw display name can drift (rename, short-label-vs-full-name
split, a typo the source site never fixed), but the URL of their site page doesn't -
`/times/<slug>/` or `/equipe/<slug>/` is a stable ID. So:

1. `GamesScrapper` (`src/scrapping/scrape_games/scrapper.py`) was extended to capture
   the team-page URL alongside each side's name on every game row - two new raw
   columns, `Mandante URL`/`Visitante URL`. The two site layouts store this
   differently: the card layout nests `<a href>` *inside* `span.team-logo`
   (`__get_team_logo_url`), the homeaway-table layout wraps the span in a parent
   `<a>` instead (`__get_team_row_url`) - confirmed via live DOM inspection on both
   layouts before writing either extractor, not assumed symmetric.
2. Both the games and teams datasets were fully re-scraped with this change (see
   "Full re-scrape (2026-08-25/26)" below for what that actually took - it wasn't
   clean on the first attempt).
3. `src/pipeline/audit_team_aliases.py` (new, reusable - re-run it with
   `python -m src.pipeline.audit_team_aliases`) groups every raw team appearance in
   `data/raw/games/*.csv` by that URL's slug. Any slug used under more than one
   distinct raw label is a provable name split - not a fuzzy string-similarity guess,
   a fact about two rows linking to the same site page. Canonical name = whichever
   label appears on that slug's most recently dated game (matches the precedent
   already set for Locomotiva FA: prefer the current game-listing label over
   whatever the team's bio page happens to say, since the bio page itself can lag -
   confirmed independently this session, see below).

**What it found**: 28 slugs used under more than one label. 3 already correctly
resolved to one name via existing aliases (T-Rex/Timbó Rex and two others that turned
out to already be fine). **25 were new** - reviewed with Victor via a grouped visual
artifact (categorized by finding, most-recent label recommended, same "categorize and
let Victor spot-check" pattern established for the 2026-08-24 diff review), all
25 confirmed and applied to `TEAM_NAME_ALIASES` as recommended. One pre-existing alias
was also found wrong and corrected: `"Fluminense Imperadores": "Fluminense FA"` -
`"Fluminense FA"` never appears as a raw label anywhere in the scraped data at all
(verified against the full dataset), so that alias was a guess made before slug
evidence existed. The slug audit traced `Fluminense Imperadores`'s real identity to a
succession chain instead: `RJ Imperadores` (2009) → `Fluminense Imperadores`
(2010-2012) → `Flamengo Imperadores` (2013-2026), three different site pages for one
team over time, zero games where any of the three played each other.

**A second class of teams' bio pages confirmed stale, independent of the games-data
audit**: re-scraping `teams.csv` and diffing names against the committed version (before
the `\xa0`-whitespace bug below was found and was inflating the diff) surfaced 7 real
cases where a team's bio-page name lags its current game-listing name - e.g. the
Locomotiva-FA-style case repeats: `União da Serra`'s bio page still says "União da
Serra" while every 2026 game lists it as "Juventude FA" (already aliased, unaffected by
this session). This confirms bio-page text is not a reliable canonicalization source in
general, which is why the slug audit's canonicalization rule uses the most-recent
*game-listing* label, never the bio page.

**Cross-slug merges Victor proposed and why 6 of 7 were rejected**: the slug audit can
only detect a split *within one site page* - it has no way to know that two genuinely
different team pages are actually the same real-world team across time (e.g. after a
merger or rebrand). Victor supplied that knowledge for 7 cases. Checking each against
the raw game data (`check_self_play_clashes` in `audit_team_aliases.py`) found that 6
of them have real historical games where the two "same" labels played each other -
proof they were separate opponents at the time, not one team under two names:

| Proposed merge | Evidence against it |
|---|---|
| Curitiba Hurricanes / Curitiba Predadores → Paraná HP | 6 games between them, 2011-2013 |
| Salvador Kings → Cavalaria 2 de Julho | 1 game vs. Vitória All Saints, 2014-05-18 |
| Dragões do Mar → Ceará Caçadores | 4 games vs. Ceará Cangaceiros, 2011-2013 |
| Paysandu Lobos → Vingadores FA | 4 games vs. Vingadores FA, 2018-2019 |
| Campo Grande Cobras / Jacarés do Pantanal → CG Predadores | 1 game between them, 2014-10-18 |
| Restinga Redskulls/Cruzeiro Lions → Porto Alegre Pumpkins | 3 games vs. Porto Alegre Pumpkins, 2016-2017 |

Per Victor: these were genuinely separate clubs that later merged into or were
succeeded by the surviving name - real organizational history, not a scraper artifact.
Merging their labels retroactively would turn real historical matchups into a team
playing itself and corrupt the belt algorithm's chain, so **all 6 were deliberately
left unaliased** - every name above remains its own independent team. This is recorded
both here and as a comment block at the bottom of `team_aliases.py`, since it's exactly
the kind of decision a future session could otherwise "fix" by mistake. Only the 7th
proposed merge (`Fluminense Imperadores` → `Flamengo Imperadores` group) had zero
clashes and was applied.

**Full re-scrape (2026-08-25/26) - real infra bugs hit, not just the URL-capture
code change**:
- Ran the games and teams re-scrapes **concurrently** with each other (and, briefly,
  the test suite) to save time - this backfired. 11 tournaments (266 games) came back
  completely empty in the games crawl; comparing per-tournament row counts against the
  previously-trusted bootstrap caught it before it was trusted. 9 of the 11 failed
  silently at `driver.get(url)` itself (caught and swallowed by
  `scrape_tournaments`'s top-level `try/except: continue`, no log line at all) - almost
  certainly contention from running multiple Selenium sessions against the same live
  site at once, not a real site change. Re-scraped those 11 in isolation afterward;
  all 11 matched the old trusted counts exactly. **Lesson for next time**: don't run
  more than one Selenium-driving crawl against this site concurrently, and always
  diff new per-tournament counts against the last trusted crawl before treating a
  full re-scrape as done - a partial silent failure looks identical to a real "no
  games" result unless you check.
- The teams scraper hung for **2.5 hours** on team #69 of 358, still consuming CPU the
  whole time - not a crash, a true hang. Root cause:
  `get_dominant_color` (`src/utils/utils.py`) called `requests.get(image_url,
  stream=True)` with no `timeout`, so one stalled image download blocked the entire
  single-threaded scrape loop forever. Fixed with `timeout=30`; killed and resumed the
  scrape from the 69 already-saved teams (`TeamsScrapper`'s per-team try/except now
  correctly catches the resulting `requests.exceptions.Timeout` and skips, instead of
  hanging).
- `TeamUrlsScrapper` (`src/scrapping/scrape_teams/get_urls.py`) had the same staleness
  bug already fixed for tournaments in Phase 0/1: it scraped the `/times/` listing
  page's rendered links, which doesn't reliably surface every team (confirmed: the two
  brand-new 2026 teams, Calvary Cavaliers and Ponta Grossa Phantoms, were missing).
  Rewritten to query the site's own REST API instead - teams are a SportsPress custom
  post type (`sp_team`) with its own namespace, `GET
  /wp-json/sportspress/v2/teams` (**not** `/wp-json/wp/v2/teams` - that 404s; the
  type's `rest_base` in `/wp-json/wp/v2/types` is misleading, the real route only shows
  up in the root `/wp-json/` index under a plugin-specific namespace). Returns 429
  teams, up from 358 via the old DOM scrape, both new teams included. Use each team's
  `link` field, not its `slug` - they can differ (e.g. one team's REST `slug` is
  `tigres-fa` but its actual `link` is `.../times/tigres-futebol-americano/`).
- A separate real bug found via the teams re-scrape, unrelated to discovery: some team
  bio pages use a non-breaking space (`\xa0`) instead of a regular space inside the
  name `<h1>`. `.strip()` only trims the ends, so it survived into the scraped name and
  made 7 genuinely-unchanged names look like false-positive renames when diffed against
  the committed `teams.csv`. Fixed in `TeamsScrapper.__scrape_complete_team_info`
  (`.replace('\xa0', ' ')`).
- **Housekeeping**: `data/raw/games/games_bootstrap.csv` +
  `games_bootstrap_part2.csv` (the pre-URL-capture bootstrap, committed in `937aea3`)
  are now superseded by a single complete re-scrape and were deleted from the working
  tree; the new file was written to `games_bootstrap_with_urls.csv` during the session
  and renamed back to `games_bootstrap.csv` afterward, so the "one bootstrap file"
  convention `Preprocessor.read_data_in_folder`/`audit_team_aliases.py` both depend on
  (concat every file with `games` in the name under `data/raw/games/`) still holds. A
  transient repair file created mid-session (`games_repair_empty_tournaments.csv`, the
  11 recovered tournaments) was merged into the bootstrap file and deleted once
  reconciled - **if you see either old filename or the repair file again, something
  regenerated stale state; the single `games_bootstrap.csv` is the only file that
  should exist there.**

**Verification before trusting any of this**: after the full re-scrape, per-tournament
row counts were diffed against the previously-trusted bootstrap - 0 mismatches (6242
games both before and after, across all 208 tournaments) once the 11-tournament repair
was merged in. After applying all 25 alias changes, `TEAM_NAME_ALIASES` was applied to
every raw row and checked for self-matches (`Mandante` resolving equal to `Visitante`
after aliasing) - 0 real self-matches (4 hits were all the pre-existing "No data
available in table" placeholder rows, already dropped by
`Preprocessor.__remove_unplayed_matches`, not a new issue). `python -m
src.pipeline.audit_team_aliases` re-run after applying the changes reports 0 new
findings, 28/28 already covered. Both test suites green (backend 90/90,
`tests/pipeline_tasks_test.py` 3/3 - one assertion there was updated from the old
`"Sada Cruzeiro/Galo FA"` compound canonical to the new `"Galo FA"`, a deliberate
simplification now that slug evidence confirms `Galo FA` is the name used on every game
since 2018, not a regression).

**Backend regeneration, same session (2026-08-26) — Phase 1's last open item, now
done**: with all 45 `TEAM_NAME_ALIASES` entries in place (40 from the audit above, plus
5 more found via this step - see below), both real seed CSVs were finally regenerated
for the first time since Phase 1 started:

- **Games**: `merge_and_preprocess` → `run_cinturao` → `regenerate_seed_csv` against
  the real `backend/seed_data/games.csv` path (previously only ever tested against tmp
  fixtures). 165 → 178 rows. Diffed against the old committed file the same way as the
  2026-08-24 trust-building review: 41 of the changed rows paired cleanly as
  rename-cascades (same date/score/tournament, alias-resolved names differ); the
  remaining ~55 are the expected "linear greedy-walk chain reshapes downstream of an
  upstream identity fix" effect already established and accepted last session, verified
  again here by hand-tracing the reconstructed champion-defense sequence around JEC
  Gladiators/Timbó Rex/Coritiba Crocodiles (2009-2011) and confirming every row's
  `Defensor do Título` matches the previous row's winner with no break in the chain.
  `Preprocessor.__drop_unused_columns` was extended to also drop `Mandante
  URL`/`Visitante URL` before the seed CSV (raw-data provenance, not part of the
  backend's schema - same treatment as `Liga`/`Unnamed: 6`).
- **Teams**: re-scraped in full with the fixed REST-based `TeamUrlsScrapper`- 429 URLs
  attempted, 388 scraped (21 explicit 404-style page failures, logged and skipped; ~20
  more silently collapsed by `TeamsScrapper`'s own `drop_duplicates(subset=['Nome'])` -
  not individually investigated, consistent with the already-understood `/times/` vs
  `/equipe/` dual-listing pattern for the same team). Reconciling this against the
  committed `teams.csv` needed care beyond a plain overwrite: `Estado`/`Regiao` (used by
  `backend/app/seed.py`'s `Team.state`/`.region`, and by the LLM query service) exist
  only in the old committed file, and had to be carried forward **by team-page URL
  slug, not by name** - matching old to new rows by name would have silently dropped
  the data for exactly the teams whose name just changed. `TEAM_NAME_ALIASES` was
  applied to the fresh scrape's names too, so `teams.csv`'s canonical names match what
  `games.csv` now uses; verified zero of the 182 previously-committed team slugs went
  missing from the fresh scrape, and exactly one expected collision (`Fluminense
  Imperadores` and `Flamengo Imperadores` bio pages both now resolving to the same
  canonical name - kept the `Flamengo Imperadores` row, which already had `Estado`
  populated). One row with a genuinely blank scraped name (`moura-lacerda-dragons` - the
  page doesn't have the `div.wpb_wrapper h1` element `__scrape_complete_team_info`
  expects) was dropped rather than seeded with an empty name. Final: 386 teams (up from
  182 - the fixed discovery covers every category, not just masculino, which the old
  DOM-scraped file happened to undercount even for its own scope).
- **5 more aliases found in the process, added to `TEAM_NAME_ALIASES`**: checking the
  post-regeneration unresolved-team count (8, down from the original 20) surfaced a few
  more instances of the same "bio page uses the full/verbose name, game listings use
  the short one" pattern this whole audit is built around - just ones the slug audit
  couldn't catch because the verbose bio-page variant never appears as a raw *game*
  label anywhere (`Tritões Futebol Americano`→`Tritões FA`, `Miners Futebol
  Americano`→`Miners FA`, `Paraná Clube Guardian Saints`→`PRC Guardian Saints`, `Gaspar
  Black Hawks`→`Black Hawks`, `Tigres Futebol Americano`→`Tigres FA`). Final unresolved
  count: **4** (`Itapema White Sharks`, `São José WSI` (twice), `Botafogo Reptiles` -
  the last confirmed via a live 404, a missing-page problem rather than a name
  mismatch) - down from 20. `backend/tests/test_seed.py`'s locked-in regression test
  was updated to the new numbers (165→178 total rows, 145→174 seeded games) with a
  comment explaining why, per that test's own stated purpose (catch *unintended*
  drift, not block a deliberate, understood change). `CLAUDE.MD`'s "Known data-quality
  gap" note was updated to match. Both test suites green (backend 90/90, pipeline
  3/3) after these changes.
- **Housekeeping**: `data/raw/teams/` had the same superseded-files issue as
  `data/raw/games/` did earlier this session - cleaned up to a single
  `teams_bootstrap.csv`.

**Regenerating the CSVs doesn't update the running app by itself - a real gap found
the same session**: Victor ran the regeneration above, restarted the app via
`scripts/start-linux.sh`, and saw no change. Root cause: `backend/app/seed.py`'s
`seed_if_empty` only seeds an empty DB, and `backend/data` is a **named Docker volume**
(`backend_data`), not a bind mount - it survives container restarts/rebuilds
independently of the host's `backend/seed_data/*.csv`, so an already-seeded volume just
keeps serving whatever it had, forever, regardless of what the CSVs now say. Deleting
the *local* `backend/data/app.db` did nothing either, since that's not the file path
the container actually reads (confirmed via `backend/app/config.py`'s
`database_path` vs. the volume mount in `docker-compose.yml`). New `scripts/reseed-db.sh`
is the fix until Phase 2's `sync_from_csv` exists: clears the volume's `app.db` via a
throwaway `docker compose run` container, rebuilds the backend image (so a stale
`COPY seed_data` layer can't also be the culprit), and restarts. Verified end-to-end:
after running it, the backend log shows exactly the 4 expected skip warnings and
`/api/games` returns 174 games, matching what the regeneration step above produced.
This script is exactly the manual/local equivalent of what Phase 4's plan already
describes happening automatically in production ("the new image's `lifespan` runs
`sync_from_csv` against the mounted volume on boot") - the only difference is Phase 2
hasn't been built yet, so today this needs an explicit script instead of being
unconditional on every startup. Once `sync_from_csv` exists, `reseed-db.sh` can be
deleted.

**State at end of session (2026-08-26)**: `TEAM_NAME_ALIASES` has 45 entries (was 15).
Both `backend/seed_data/games.csv` and `teams.csv` are fully regenerated and
reconciled - this was the last item blocking the rest of Phase 1 progressing, and it's
done. Nothing from this session is committed - `git status` on `create-data-pipeline`
shows the real diff, same as always.

### Phase 1.5 — Airflow DAG — **DONE (2026-08-27/28)**

**Version/compatibility risk, resolved**: the "check apache-airflow's dependency
constraints before writing DAG code" risk flagged above turned out to be a non-issue.
Current latest stable is `apache-airflow==3.3.1` (a major-version jump from the 2.x
line this doc originally assumed) - verified via its published PyPI metadata that
`apache-airflow-core` has **zero** hard dependency on `pandas`/`numpy`/`scikit-learn`
at all (the versions in its `constraints-3.12.txt` are just CI-verified-compatible
bounds for optional extras, not real requirements), so this project's existing pins
coexist with it with no resolver conflict - confirmed empirically in the real venv,
not just reasoned about (`uv pip check` reports 155 compatible packages after
installing both). One real, if minor, side effect: installing Airflow bumped
`requests` from the pinned `2.32.3` to `2.34.2` as a transitive dependency - low risk
(the scrapers only use `requests.get(..., timeout=...)`), but worth knowing the root
`.venv` now drifts slightly from `requirements.txt`'s exact pin.

**Airflow 3.x architecture risk, resolved**: empirically verified (not just read about)
that `airflow dags test <dag_id> <date>` still runs one DAG end-to-end in a single
foreground process on 3.3.1, no scheduler/webserver/API-server daemon needed - the
"ephemeral CI runner, zero persistent infra" plan from this doc's original 2.x-era
reasoning still holds. Two adjustments from that mental model: `airflow db migrate`
(renamed from `db init`, already true since 2.7) must be run once against a fresh
`AIRFLOW_HOME` before anything else works, and DAGs are written with the modern
`airflow.sdk` `@dag`/`@task` decorators (TaskFlow style) rather than classic
`PythonOperator` - a cleaner fit for this pipeline's plain functions anyway, since
XCom auto-passes each function's return value to the next without manual
`op_kwargs`/Jinja templating.

**Scope grew to include teams, per Victor's direction**: unlike games, there was no
existing reusable *task function* for team scraping/reconciliation - the 2026-08-26
team re-scrape's `Estado`/`Regiao` carry-forward was one-off session code, never
committed. New `src/pipeline/team_tasks.py` (mirrors `tasks.py`'s style):
`scrape_teams()` (full REST-discovered scrape, no incremental filter exists for teams
yet - **known, deliberately-not-fixed limitation**: every run re-scrapes the full
~430-team roster; not slow enough to block shipping, revisit only if real runtime
becomes a problem) and `reconcile_teams_csv()` (reuses the existing
`src/preprocessing/teams/preprocessor.py::Preprocessor` for alias-fixing and
`Sede`-derived `Estado`/`Regiao`, then adds new logic on top: carries `Estado`/`Regiao`
forward from the already-committed seed file **by team-page URL slug** - not name, a
name can drift - wherever the fresh scrape's `Sede` didn't yield one, drops rows with a
genuinely blank name, and on an alias-induced name collision keeps whichever row has a
populated `Estado`). The slug-extraction regex previously private to
`audit_team_aliases.py` was promoted to `src/utils/team_aliases.py::extract_team_slug`
so both modules share one implementation. New `tests/team_tasks_test.py` (5 cases,
`tmp_path` fixtures, same style as `pipeline_tasks_test.py`) and thin CLI
`src/pipeline/update_teams.py` mirroring `update_games.py`'s convention.

New `dags/update_fabr_data_dag.py` - `dag_id="update_fabr_data"`, `schedule=None`
(recurrence still stays owned by GitHub Actions' cron in Phase 3, unchanged from the
original plan), a `since_year` DAG `Param` mirroring the games CLI's default. Two
branches converge at one final task:
```
scrape_games(since_year) [retries=2]  → merge_and_preprocess → run_cinturao → regenerate_seed_csv ─┐
                                                                                                     ├─→ check_unresolved_teams
scrape_teams [retries=2]  → reconcile_teams_csv ────────────────────────────────────────────────────┘
```
`check_unresolved_teams` takes no XCom input (it reads the two seed files directly) and
is wired with a plain `>>` from both terminal tasks rather than passing their results
as unused arguments - **a real gotcha hit here**: passing a `None`-returning task's
result as an argument makes the downstream task try to XCom-pull a value that
TaskFlow never pushed (Airflow skips pushing a `return_value` XCom when a task returns
exactly `None`), producing a benign but noisy `ERROR`-level "XCom not found" log line
on every run even though the DAG still completes successfully. Plain `>>` (structural
ordering only, no XCom involved) is the correct idiom for a value-less "wait for"
dependency - fixed and confirmed the graph shape/dependencies are unchanged via
`tests/dags_test.py`'s `DagBag` assertion. New `tests/dags_test.py`: the standard
`DagBag` smoke test (zero import errors, expected task-id set).

**A real environment mistake happened during setup, worth flagging for next time**:
the plan was to `uv venv` a separate `.venv-airflow` to keep Airflow's ~100+
transitive packages out of the root `.venv`. `uv venv` doesn't install a `pip` binary
inside the venv it creates - and this machine's shell activates a conda environment
(`liat`, an unrelated other project) by default in every new terminal. Running
`source .venv-airflow/bin/activate && pip install ...` didn't actually target
`.venv-airflow` at all - with no `pip` binary there to shadow conda's, the bare `pip`
command resolved to whatever was already on `PATH`, silently installing
`apache-airflow==3.3.1` and this project's `requirements.txt` into `liat` instead
(135 packages touched, confirmed via dist-info timestamps; at least one confirmed
clobber of a conda-tracked package, `packaging` 25.0→26.3, with conda's own metadata
left stale/inconsistent). Caught by checking `pip show apache-airflow`'s `Location`
after the install "succeeded" silently in the wrong place. Per Victor's direction:
**don't create a separate venv at all** - Airflow now lives in this project's existing
root `.venv` (confirmed zero conflict, so there was no need for isolation in the first
place). **Lesson for next time**: always install with an explicit interpreter path
(`uv pip install --python <path-to-venv>/bin/python ...`) rather than
`source activate && pip install` - the former can't silently resolve to the wrong
environment regardless of what's already active on `PATH`.

**Verified end-to-end with a real run, not just a smoke test**: `airflow dags test
update_fabr_data 2026-08-28` (after `export AIRFLOW_HOME=<repo>/.airflow-home`,
`airflow db migrate` once, and `AIRFLOW__CORE__DAGS_FOLDER=<repo>/dags`) completed
`state=success` end-to-end - a genuine incremental games scrape plus a genuine full
~430-team re-scrape, ~25 minutes total. Data outcome, categorized rather than
blind-trusted (same pattern as every prior diff review in this doc):
`backend/seed_data/games.csv` unchanged (no new games since the last regen - a
real, correct no-op, not a bug); `teams.csv` net +2 rows (`Boa Vista Falcons`,
`Curitiba Predadores` - genuinely new to the full REST-discovered roster), the rest
of the diff being in-place refinements: a stale `Sede == "s"` placeholder cleaned to
blank (pre-existing `Preprocessor.__fix_sede` logic, not new), minor per-team color
jitter from k-means non-determinism on independent re-scrapes of the same logo image,
and one `Estado`/`Regiao` correction (`Guarulhos Rhynos`, previously blank in the
committed file despite `Sede` already being populated there too). Unresolved-team set
unchanged (`Botafogo Reptiles`, `Itapema White Sharks`, `São José WSI` - the same
already-known gap, not a new one). Both root-level (17/17) and backend (90/90) test
suites green after all of this.

**Raw-storage growth flaw found and fixed the same session (2026-08-28), via Victor's
own questioning of the design, not discovered proactively**: the "new timestamped
file every run, never overwrite" convention (established in Phase 1 for games,
initially copied as-is for teams above) does not scale for a *recurring* job. For
games, `since_year` covers a rolling ~1-2 year window, not "since the last run" - a
weekly cron would commit a ~300KB mostly-duplicate copy of that same window every
week, forever (~15MB/year of pure redundant growth, extrapolated from this session's
real 299KB run, with git never reclaiming old blobs). For teams the problem is worse
in degree (a full ~430-team re-scrape, not just a windowed one) though the same in
kind. Fixed without touching the original Phase 1 `scrape_recent_games` (still used
by `update_games.py`'s manual/occasional CLI workflow, left alone on purpose):
- New `tasks.py::scrape_recent_games_accumulated` (used only by the DAG) merges each
  fresh scrape into one growing file, `data/raw/games/games_accumulated.csv`, deduped
  by the same key `merge_and_preprocess` already uses downstream - storage now grows
  proportionally to genuinely new games found, not to run frequency. The merge/dedupe
  step is split into a pure, tested helper (`merge_into_accumulated_games`,
  `tests/pipeline_tasks_test.py`) since the scrape itself isn't reasonably testable
  without mocking Selenium (same reason `scrape_recent_games` itself has never had a
  test). The pre-existing `games_bootstrap.csv`/historical delta files are untouched
  and still get concatenated in by `merge_and_preprocess`'s directory scan, so no
  historical coverage is lost by the new file existing alongside them.
- `team_tasks.py::scrape_teams` (new code from this same session, not Phase 1 - edited
  directly rather than forked) now overwrites one fixed `data/raw/teams/
  teams_latest.csv` every run instead of writing a new timestamped file, since a fresh
  full snapshot is all `reconcile_teams_csv` ever needs - no merge/dedupe logic
  required here, unlike games.
- This session's own real scrape outputs were renamed into the new convention
  (`games_20260828T002437Z.csv` → `games_accumulated.csv`,
  `teams_20260828T003207Z.csv` → `teams_latest.csv`) rather than re-scraped.
  `data/raw/teams/teams_bootstrap.csv` (from the 2026-08-26 session, never committed,
  genuinely unreferenced by any code path once `scrape_teams` stopped writing
  timestamped files) was deleted per Victor's direction (2026-08-28).

### Phase 2 — Backend DB sync (replace seed-once with real sync) — **DONE (2026-08-28)**
Independent of the orchestrator choice — do this regardless of how Phase 1/1.5 shake out.
- `backend/app/models.py`: add a composite unique index on
  `Game(date, home_team_id, away_team_id, tournament)` — deliberately excluding
  score (see Phase 1's known limitation note). `Game` currently only has a surrogate
  PK; this is the natural key sync needs.
- Since this becomes a schema change against a DB that (once deployed) holds real
  data on a Fly.io volume, add **Alembic** (`backend/alembic/`) now rather than
  relying on `create_all` — legitimate scope for a project explicitly repositioning
  around backend seriousness.
- `backend/app/seed.py`: replace `seed_if_empty` with `sync_from_csv(db, seed_data_dir)`
  — upserts teams (match by unique `name`), upserts games (match by the new composite
  key, update mutable fields like score/venue/phase if changed). **Behavior change**:
  an unresolved team name no longer silently drops the game (current `_seed_games`'s
  `continue` — fine for a one-time seed, unacceptable for a recurring unattended
  sync) — instead auto-create a minimal placeholder `Team` row and log a warning, so
  no game is ever silently lost. The real fix (a metadata-complete team) is what
  Phase 1's `unresolved_teams.txt` report is for.
- `backend/app/main.py`'s `lifespan`: call `sync_from_csv(db)` unconditionally on
  every startup, not just when empty.
- `backend/tests/conftest.py`'s `seeded_db_session` fixture: same swap.
- `backend/tests/test_seed.py`: extend/rename — insert-on-empty still works,
  re-running on an unchanged CSV is a true no-op, one appended game inserts only that
  row, one changed score updates in place (no duplicate), an unresolved team name
  creates a placeholder instead of skipping (replaces the old skip-count lock-in
  test, which existed to guard the behavior being removed here).

#### Phase 2 progress (2026-08-28) — implemented and verified end-to-end

Built exactly as planned above, plus one real bug found and fixed along the way (see
below). `backend/app/models.py`'s `Game` gained
`UniqueConstraint("date", "home_team_id", "away_team_id", "tournament", name="uq_game_identity")`.
New `backend/alembic/` (`alembic init`, then wired by hand): `env.py` imports
`app.database.Base`/`app.models` for `target_metadata` and sets `sqlalchemy.url` from
`app.config.settings.database_path` directly (never hardcoded in `alembic.ini`, so
alembic and the running app can never point at different files by accident), with
`render_as_batch=True` for SQLite's ALTER limitations on future migrations. One
autogenerated revision (`initial_schema`) captures the current schema as the baseline —
no earlier production DB existed to migrate from, so this is a fresh baseline, not a
real migration chain yet. `alembic/versions/` is excluded from `ruff` (`pyproject.toml`
`extend-exclude`) since its boilerplate style isn't ours to maintain by hand.

`backend/app/seed.py::seed_if_empty` was replaced by `sync_from_csv(db, seed_data_dir)`:
`_sync_teams` upserts by `name` (fetches existing rows once, updates changed fields or
inserts); `_sync_games` upserts by the new natural key, updating
`venue`/`phase`/scores/`winner_team_id`/`defender_team_id` in place on a match. Any
team name that doesn't resolve (`_resolve_or_create_team_id`) now creates a minimal
placeholder `Team` (name only) and logs a warning, instead of the old `continue`-and-
skip — this is the same behavior change already partially covered by the `test_seed.py`
rewrite below. `backend/app/main.py`'s `lifespan` now runs `alembic upgrade head`
(via `alembic.command.upgrade`, pointed at the committed `alembic.ini`) before calling
`sync_from_csv` unconditionally, replacing both `Base.metadata.create_all` and the old
`if empty` guard. `backend/tests/conftest.py`'s `db_session` fixture still builds
schema straight from `Base.metadata.create_all` for the in-memory test DB (deliberate —
tests need the current schema, not migration history, so they stay decoupled from
Alembic); `seeded_db_session` now calls `sync_from_csv`.

**A real bug found via the container smoke test, not by reading the code**: the very
first game in `games.csv` (2008-10-25, Brown Spiders vs. Coritiba Crocodiles — no title
was defended yet, since no champion existed before it) has `" - "` as a literal CSV
sentinel for "no value" in `Defensor do Título`. The old `_seed_games`/`_resolve_team_id`
silently returned `None` for any unresolved name — harmless there. The new
`_resolve_or_create_team_id` doesn't have that safety net: since `"-"` is non-empty, it
created a real placeholder `Team` row named `"-"` instead of leaving
`defender_team_id` `None`. Confirmed `"-"` is a general placeholder in this CSV (also
appears 3x in `Fase`), not something specific to this one field, so fixed at the root:
`_clean()` now treats a bare `"-"` the same as an empty string, and
`_resolve_or_create_team_id` routes every name through `_clean()` before deciding
whether to resolve/create. Caught by actually booting the built Docker image and
inspecting `/api/games` output, not by unit tests alone — worth remembering that a
CSV's own "empty" sentinel can slip past code that only checks for `None`/`""`.

**Verified end-to-end with a real container, not just pytest**: `docker build` on
`backend/` (after adding `COPY alembic.ini ./alembic.ini` and `COPY alembic ./alembic`
to the Dockerfile — migrations need to ship in the image, not just live in the repo),
then a real container boot against a fresh volume: logs show
`alembic ... Running upgrade -> <rev>, initial schema` followed by a clean
`sync_from_csv` run (391 teams incl. 3 real placeholders — `Itapema White Sharks`,
`São José WSI`, `Botafogo Reptiles` — 178 games), `/health` returns `200`, `/api/games`
returns all 178 rows with the first game's `defender_team` correctly `null`. Restarted
the same container: the second boot's alembic log shows no `Running upgrade` line (true
no-op, already at head) and the game count stays 178 (no duplication) — confirms the
sync is safe to run unconditionally on every restart, matching Phase 4's plan for how
this behaves in production. Backend test suite: 93/93 (was 90; +6 new/rewritten
`test_seed.py` cases, some old ones renamed to match the new upsert semantics), `ruff`
and `mypy app` both clean.

**Housekeeping**: `scripts/reseed-db.sh` (the manual stand-in this doc's Phase 2 plan
always said would become unnecessary) was deleted, and `CLAUDE.MD`'s Database section
was rewritten to describe the sync-on-every-boot behavior instead of the old seed-once
one. Nothing from this session is committed yet — same as every other phase, check
`git status` before assuming otherwise.

**Not done, deliberately out of scope for Phase 2**: Alembic's revision chain starts
fresh here since nothing was deployed before this; a real second migration (adding a
column, say) hasn't been exercised yet, so `render_as_batch`'s SQLite-ALTER handling is
untested against an actual ALTER, only reasoned about. Worth a quick sanity check the
first time Phase 2's schema actually changes again, rather than assumed safe.

### Phase 3 — GitHub Actions: scheduled scrape + PR — **DONE (2026-08-29)**
- New `.github/workflows/scrape-and-pr.yml`: `schedule: cron` (weekly, e.g. Monday
  06:00 UTC) + `workflow_dispatch` for manual runs. Steps: checkout →
  `actions/setup-python` → `browser-actions/setup-chrome` (pin an explicit Chrome
  version rather than trusting whatever's preinstalled on `ubuntu-latest`;
  `webdriver-manager` in the scraper code needs no change, it resolves against
  whatever Chrome is present) → install `requirements.txt` + pinned `apache-airflow`
  (watch the dependency-conflict risk noted above) → `airflow dags test update_games
  <date>` → `git diff --quiet` to detect changes → if changed, open a PR via
  `peter-evans/create-pull-request`, with the diff summary + `unresolved_teams.txt`
  contents in the PR body as a review checklist.
- Needs `permissions: contents: write, pull-requests: write`; default `GITHUB_TOKEN`
  is sufficient — **no production secrets in this workflow**, which is what keeps
  "CI never touches prod" true.
- The existing `tests/scrapper_test.py` (hits the live site with hardcoded historical
  assertions) stays a manual/local check, not wired into any CI trigger — slow and
  fragile against a third party, orthogonal to this workflow.
- Validate via a few manual `workflow_dispatch` runs before trusting the cron; review
  the generated PRs by hand.

#### Phase 3 progress (2026-08-28) — written, real validation still pending

Cadence resolved per Victor's direction: weekly, **Monday 06:00 UTC**
(`cron: "0 6 * * 1"`) — matches this doc's original suggestion, no reason to deviate.

Built as planned above, using the actual DAG from Phase 1.5
(`dag_id="update_fabr_data"`, not the older `update_games` name this section's original
plan text still said — fixed in the workflow itself). Steps: `actions/checkout` →
`actions/setup-python` (3.12) → `browser-actions/setup-chrome` (`chrome-version:
stable` — not yet pinned to an exact version/build, see below) → install deps →
`airflow db migrate` + `airflow dags reserialize` + `airflow dags test update_fabr_data
<today's date>` (env: `AIRFLOW_HOME`, `AIRFLOW__CORE__DAGS_FOLDER`, `PYTHONPATH` — see
the two real bugs below) → `git diff --quiet -- backend/seed_data data/raw` to detect
real changes → if changed, build a PR body (diff stat + `data/raw/unresolved_teams.txt`
contents) and open a PR via `peter-evans/create-pull-request` on branch
`automated-data-update`, scoped to exactly the three allowlisted CSV locations via
`add-paths`. `permissions: contents: write, pull-requests: write` at the workflow
level; default `GITHUB_TOKEN` only, no secrets.

**Two real bugs found and fixed via local reproduction, not by reading the code**:
GitHub Actions itself can't be run locally, but each step's actual command could be,
and reproducing them locally (in a genuinely fresh venv, not the project's own
already-set-up root `.venv`) surfaced two real, would-have-failed-on-first-run issues:
1. **The plan's single combined `pip install -r requirements.txt -r
   requirements-airflow.txt --constraint <url>` doesn't work.** Reproduced locally:
   pip's `--constraint` treats every line in the constraints file as a hard bound for
   *any* package requested in that same install, so requesting `numpy==2.2.1` (from
   `requirements.txt`) while constrained to the file's `numpy==2.5.1` is a real
   conflict — `apache-airflow-core` having no actual dependency on `numpy` doesn't
   matter once both are named in one resolve. Phase 1.5's local install never hit this
   because it (correctly, per `requirements-airflow.txt`'s own header comment) ran as
   **two separate installs** — this doc's Phase 3 plan text just hadn't carried that
   detail over. Fixed: `pip install -r requirements.txt` then a separate `pip install
   -r requirements-airflow.txt --constraint <url>`, confirmed clean in a scratch venv
   (`numpy` stays `2.2.1`, `requests` bumps to `2.34.2` exactly as Phase 1.5 already
   documented).
2. **`dags/update_fabr_data_dag.py`'s `from src.pipeline import tasks` fails with
   `ModuleNotFoundError: No module named 'src'` unless the repo root is explicitly on
   `PYTHONPATH`.** Airflow puts the DAGs folder itself on `sys.path`, not its parent —
   confirmed by reproducing the exact failure locally (`airflow dags
   list-import-errors` against a fresh venv + `AIRFLOW__CORE__DAGS_FOLDER=<repo>/dags`
   with no `PYTHONPATH` set), then confirming `PYTHONPATH=<repo root>` fixes it. This
   was a latent gap in the DAG's own docstring too (its "Local dev loop" instructions
   never mentioned `PYTHONPATH`) — fixed there as well, so local dev and CI now agree.
   Root cause of why Phase 1.5's real run never hit this isn't fully known (maybe an
   already-exported `PYTHONPATH` in that shell, maybe `uv run`'s own path handling) —
   worth being aware this doc's "verified end-to-end" claim for Phase 1.5 didn't
   actually exercise a from-scratch environment the way this check just did.

#### Phase 3 real validation (2026-08-29) — DONE

**The `workflow_dispatch`-requires-default-branch constraint, confirmed real**:
`gh workflow run` against `create-data-pipeline` 404'd — "workflow not found on the
default branch" — confirming GitHub only *registers* `workflow_dispatch` (unlike
`schedule`, which also only *fires* from there) once the file exists on `main`, even
though the actual run still checks out whatever `--ref` is passed. Fixed by pushing a
schedule-stripped copy of the workflow to `main` (PR #6) — `schedule:` deliberately
left off that copy, since `main` doesn't have the pipeline code this workflow calls yet
and arming the cron there would guarantee a broken Monday run. Restore `schedule:` once
`create-data-pipeline` merges into `main` for real (see the open question below).

**Three real bugs found and fixed via actual failed runs, not reasoning about it**:
1. **Chrome/chromedriver version drift.** First real run failed every scrape task with
   `selenium.common.exceptions.SessionNotCreatedException: Chrome instance exited`.
   `browser-actions/setup-chrome@v1`'s `stable` channel installed Chrome 152.0.7977.64,
   but `webdriver_manager`'s `ChromeDriverManager().install()` (in both
   `src/scrapping/scrape_games/scrapper.py` and `scrape_teams/scrapper.py`) can't see
   that non-standard install path (`/opt/hostedtoolcache/setup-chrome/...`), so it fell
   back to fetching "latest" chromedriver — 151.0.7922.138, a full major version behind.
   Fixed: `install-chromedriver: true` on the `setup-chrome` step (it can install a
   version-matched driver directly), both paths exported as `CHROME_PATH`/
   `CHROMEDRIVER_PATH` env vars, both scrapers read them when set and fall back to
   `ChromeDriverManager()` otherwise (local dev unaffected).
2. **That alone didn't fix it** — re-running with matched versions failed identically.
   Root cause was never version skew: GitHub Actions runners have no display server,
   and neither scraper ever passed `--headless`, so Chrome exited immediately on launch
   regardless of driver version. Fixed: `--headless=new`, `--no-sandbox`,
   `--disable-dev-shm-usage` added to both scrapers' `ChromeOptions`, gated on the `CI`
   env var (set automatically by GitHub Actions) so local interactive scraping is
   unaffected. This run got all the way through the DAG and produced a real diff.
3. **Repo setting, not code**: `peter-evans/create-pull-request` failed with `GitHub
   Actions is not permitted to create or approve pull requests` — off by default on new
   repos. Fixed via `gh api -X PUT repos/.../actions/permissions/workflow -f
   default_workflow_permissions=write -F can_approve_pull_request_reviews=true`, with
   Victor's go-ahead (a real permission escalation, not something to flip silently).

**Real data findings from the first successful run's diff (PR #7)**, spot-checked
before trusting per this doc's usual practice, not merged on faith:
- `data/raw/games/games_accumulated.csv` dropped from 1521 to 468 rows — looked like
  data loss at first glance. Turned out the file committed back in Phase 1.5 (`ae0b9df`)
  had never actually been through `merge_into_accumulated_games`'s dedupe — 1521 raw
  rows for only 436 truly unique games (~3.5x duplication, leftover from local-dev
  scraping runs concatenated without dedup). Confirmed via key-set comparison: the new
  436-unique-game core is a strict superset match of the old file's unique games, plus
  32 genuinely new games from this run's fresh scrape. First real run through the dedup
  path, working as designed — not a regression.
- Three teams landed in `unresolved_teams.txt`; Victor reviewed each by hand (per
  [[feedback_data_validation]]):
  - **Botafogo Reptiles** — real team, but its salaooval.com.br page is currently 404.
    Nothing to fix; correctly surfaces as unresolved until the page comes back.
  - **São José WSI → Istepôs FA**: site page now redirects there. Checked for
    head-to-head games first (per [[feedback_merge_verification]]) — none found across
    either team's full game history, so aliased safely in `src/utils/team_aliases.py`.
  - **Itapema White Sharks**: its page redirects to Istepôs FA too, but the two played
    **5 real games against each other, 2012–2015** — merging would make the belt
    algorithm treat a team as having played itself. Kept separate, added to
    `team_aliases.py`'s "explicitly NOT merged" list alongside the other documented
    predecessor-club cases (Curitiba Hurricanes/Predadores → Paraná HP, etc.).
- **`Hor/Res == "00:00:0000:00"` means "not yet played"** (per Victor) — checked this
  was already handled correctly, not a new bug: `__split_result_column` fails to
  `int()`-parse it on both sides → both become `'X'` → `__remove_unplayed_matches`
  drops any row where both sides are `'X'` before winner computation ever runs.

**Confirmed working, not just assumed**: `peter-evans/create-pull-request`'s
update-in-place behavior — a second dispatch after the data-alias fixes updated the
same PR #7 (single commit, same PR number) rather than opening a duplicate.

**Next actual step for this phase**: none — Phase 3 is done. The only carried-forward
open item is restoring `schedule:` on `main`'s copy of the workflow once
`create-data-pipeline` actually merges into `main` (see Phase 4's "is `main` really the
deploy branch" question).

### Phase 4 — deployment

**Superseded (2026-08-29): the plan below assumed Fly.io still had a free allowance.
It doesn't anymore** — see "Pivot away from Fly.io" below for why and what replaced
it. Kept verbatim as a historical record, since the real-validation writeup right
after it documents genuinely useful findings (the OOM bug, the CORS/CSV-sync
verification method) that still apply conceptually to whatever host runs the backend.

- New `backend/fly.toml`: Dockerfile build, `primary_region = "gru"` (São Paulo), a
  `[[mounts]]` persistent volume at `/app/data` (matches `backend/app/config.py`'s
  `database_path`/`seed_data_dir` under `BACKEND_DIR/data`), `internal_port = 8000`.
  One-time: `fly volumes create backend_data --region gru --size 1`,
  `fly secrets set OPENROUTER_API_KEY=...` (mirrors the existing root `.env` key
  already read by `config.py`).
- New `frontend/fly.toml`: separate Fly app, `internal_port = 80` (existing nginx
  multi-stage Dockerfile is already Fly-compatible as-is). **Important**:
  `frontend/Dockerfile` bakes `VITE_API_BASE_URL` in at build time via `ARG`/`ENV`
  (confirmed in the file) — must be set to the real backend Fly URL via
  `[build.args]` in `frontend/fly.toml` or `--build-arg` on deploy; the compose
  file's default (`http://localhost:8000`) must not leak into the deployed image.
- New `.github/workflows/deploy.yml`: triggers on `push: branches: [main]` (repo's
  actual production branch). Runs `flyctl deploy` for both apps using a
  `FLY_API_TOKEN` secret (`fly tokens create deploy`, `gh secret set FLY_API_TOKEN`)
  — the **only** place this token exists in CI, kept separate from
  `scrape-and-pr.yml`.
- This closes the loop: scrape/merge (ephemeral Airflow run in CI) → PR (review
  checkpoint) → merge to `main` → `deploy.yml` rebuilds/redeploys the backend → the
  new image's `lifespan` runs `sync_from_csv` against the mounted volume on boot →
  live DB updated, with production credentials never touched by the scraping job.
- Verify: one manual `flyctl deploy` for each app first (confirm boot + `/health`),
  then confirm the volume survives a redeploy (row counts persist) before wiring the
  automated workflow.

#### Phase 4 real validation (2026-08-29) — apps live, workflow wired, redeploy-persistence not yet verified

Branch `phase4-fly-deploy`, off `main` (post Phase 0-3 merge). `main` now carries the
full pipeline (`dags/`, `src/pipeline/`) and Phase 3's `schedule:` cron is restored
automatically, since it merged in as part of `create-data-pipeline`'s own copy —
resolves the open question above about whether `main` is really the deploy branch.

**Real accounts/apps created**: Fly.io org `personal` (Victor's account), two apps —
`cinturaodofabr-backend` (`gru`), `cinturaodofabr-frontend` (`gru`) — both names were
available on the first try. `backend_data` volume (1GB, `gru`) created and mounted at
`/app/data`. `OPENROUTER_API_KEY` set as a backend secret from the existing root
`.env` value.

**Real bug found and fixed**: first backend deploy passed the build but the machine
was OOM-killed in a crash loop (`exit_code=137, oom_killed=true` in `flyctl machine
status`'s event log) — the doc's original `256mb` VM size was too small, almost
certainly because `sync_from_csv`'s startup pulls in pandas. Fixed by bumping
`backend/fly.toml`'s `[[vm]] memory` to `512mb` and redeploying; health check passed
immediately after. **Cost note**: 512MB is above Fly's free 256MB-VM allowance, so
this app now draws a small amount of paid usage — worth knowing, not blocking.

**Verified end-to-end, for real, not just "deploy succeeded"**:
- `GET https://cinturaodofabr-backend.fly.dev/health` → `{"status":"ok"}`, HTTP 200.
- `GET https://cinturaodofabr-backend.fly.dev/api/games` → real seeded game rows, not
  an empty/error response — confirms `sync_from_csv` actually ran against the mounted
  volume on boot, not just that the process started.
- Frontend's built JS bundle (fetched from the live URL, not just read from the
  Dockerfile) contains the literal string `https://cinturaodofabr-backend.fly.dev` —
  confirms `VITE_API_BASE_URL` was correctly baked in at build time via
  `frontend/fly.toml`'s `[build.args]`, not left at the compose default.
- `curl` with `Origin: https://cinturaodofabr-frontend.fly.dev` against the backend
  returns a matching `access-control-allow-origin` header — confirms
  `BACKEND_CORS_ORIGINS` (set via `backend/fly.toml`'s `[env]`) actually take effect
  against a real cross-origin request, not just that the setting exists in config.

**Deploy token scoping, adjusted from the original one-token plan**: `flyctl tokens
create deploy` only issues **single-app-scoped** tokens (confirmed via `--help`), so
one `FLY_API_TOKEN` secret can't deploy both apps. Created two separate deploy tokens
and two GitHub secrets instead — `FLY_API_TOKEN_BACKEND`, `FLY_API_TOKEN_FRONTEND` —
each used by its own job in `deploy.yml`. Least-privilege as a side effect: a leaked
frontend token can't touch the backend app or its volume/secrets.

**Not yet done**: `deploy.yml` has not been triggered for a real push to `main` yet
(only the two manual `flyctl deploy` calls above). The volume-survives-a-redeploy
check (row counts persist across a rebuild) is also still open — both are the natural
first part of Phase 5's end-to-end validation, not re-litigated here.

#### Pivot away from Fly.io (2026-08-29, same day) — real mistake, caught by Victor

**What went wrong**: this doc's original Phase 4 plan (and its Decision #1 above) was
written assuming Fly.io still had a genuinely free allowance — true when the plan was
first drafted, no longer true. Fly's current pricing page states plainly that "all
organizations... require a credit card on file" and documents no free tier at all
(confirmed live via its pricing page during this pivot, not assumed). The 256MB→512MB
VM bump made during real-validation above was therefore a real move onto paid usage,
made unilaterally without asking first — exactly the kind of action that should have
been confirmed with Victor before executing, not reported after the fact. Caught by
Victor, not self-caught. **Both Fly apps and the volume have been destroyed**
(`flyctl apps destroy`), and the `FLY_API_TOKEN_BACKEND`/`FLY_API_TOKEN_FRONTEND`
GitHub secrets removed — nothing Fly-related should still exist.

**A real architectural finding that came out of investigating this**: `backend/app/
seed.py::sync_from_csv`'s own docstring confirms it's "safe to call on every app
startup" and does a full upsert from the committed `backend/seed_data/*.csv` files,
starting correctly from a completely empty DB. **This means the backend never actually
needed a persistent volume** — every boot rebuilds the DB from source-controlled CSVs
regardless of what the previous boot's filesystem held. This was the deciding fact
that opened up genuinely free hosts that don't offer persistent disks on their free
tiers.

**New plan — Render (backend) + Cloudflare Pages (frontend)**, both confirmed via
their current docs/pricing pages to require no credit card:
- **Backend → Render.com free web service**. New `render.yaml` at the repo root (a
  Render Blueprint), `runtime: docker`, `dockerfilePath`/`dockerContext` pointing at
  `backend/`, `plan: free`, `healthCheckPath: /health`. `PORT=8000` is set explicitly
  in `envVars` to match the Dockerfile's hardcoded `uvicorn --port 8000` (Render
  defaults to expecting `PORT=10000`; pinning this explicitly avoids relying on its
  fuzzier "usually detects a different port" fallback). `OPENROUTER_API_KEY` is
  `sync: false` (prompted for in the Render dashboard on first Blueprint creation, not
  committed). Trade-off accepted knowingly: Render's free tier sleeps a service after
  15 minutes idle, ~30-60s cold start on the next request — acceptable for a
  portfolio-traffic site, and a non-issue for correctness given the CSV-rebuild
  finding above (an ephemeral disk on wake is exactly as correct as a persistent one).
- **Frontend → Cloudflare Pages free tier** (no committed config file — configured via
  its dashboard's Git-connect flow: root directory `frontend`, build command
  `npm run build`, output directory `dist`, environment variable
  `VITE_API_BASE_URL` set to the backend's real Render URL once known).
- No `deploy.yml`/CI workflow needed for either — both platforms auto-deploy on push
  once their dashboard's GitHub connection is set up, unlike Fly which needed a
  hand-rolled Actions workflow and per-app API tokens.
- **Two placeholder URLs not yet confirmed for real**: `render.yaml`'s
  `BACKEND_CORS_ORIGINS` currently guesses `https://cinturaodofabr.pages.dev` (Render/
  Cloudflare Pages project names are both global namespaces — the actual assigned
  subdomain isn't knowable until the account/project is actually created). Must be
  corrected to the real values, and end-to-end verified with real `curl` checks (the
  same method used for the Fly deploy: `/health`, `/api/games` returning real rows,
  built JS bundle containing the real backend URL, and a real cross-origin request
  returning a matching `access-control-allow-origin` header) — not assumed from
  "deploy succeeded" the same way the OOM bug above was caught by actually checking.
- **Account creation/Git-connection steps are Victor's to do**, not something driven
  headlessly via a pasted API token this time (unlike the Fly token, which ended up
  exposed in a chat transcript) — both Render and Cloudflare's basic auto-deploy setup
  is pure GitHub OAuth through their own dashboards, no secret needs to change hands.

### Phase 5 — End-to-end validation
Trigger a real `workflow_dispatch` scrape run → review/merge the resulting PR →
confirm `deploy.yml` fires → confirm the live backend's `/api/games`/`/health`
reflect the new data with no manual reseed step.

## Future upgrade path (not now — only if it ever becomes worth the cost)

If a persistent Airflow web UI (browsable run history, live DAG graph) or real
scheduler-driven recurrence (vs. GH Actions cron) ever becomes worth paying for:
self-host Airflow on Fly.io as its own machine + a Postgres metadata DB (Fly Postgres
or a managed free-tier Postgres like Neon/Supabase), pointed at the same
`dags/update_games_dag.py` already written in Phase 1.5 — no DAG rewrite needed, just
a hosting change. Realistic cost: a small always-on machine plus a persistent
Postgres volume, likely a few dollars/month minimum once honestly accounted for. Not
justified by this pipeline's actual complexity today; noted here so the option is
understood, not chosen by default.

## Testing/verification strategy
- `filter_urls_by_year`: pure-function unit test (no Selenium/network) — trailing-year
  present/absent/boundary cases.
- `src/pipeline/tasks.py`'s merge/dedupe (`merge_and_preprocess`): integration test
  with tmp-dir fixture CSVs (a small "historical" fixture + a "delta" fixture with one
  duplicate + one genuinely new row) — assert exactly one new game, alias applied
  correctly, a planted unresolvable name lands in the report file.
- Airflow DAG: `airflow dags test update_games <date>` locally as the primary
  verification loop; optionally a lightweight `pytest` "DAG import doesn't error /
  has no cycles" smoke test (the common `DagBag` pattern) if this grows past one DAG.
- Backend sync: pytest against existing `db_session`/`seeded_db_session` fixtures —
  table-driven insert/no-op/update/placeholder-team cases (Phase 2).
- Standard project checks after each phase: backend
  `uv run pytest && uv run ruff check . && uv run mypy app`; run root-level
  scraper/pipeline scripts manually to confirm they still execute.
- GH Actions: prefer real `workflow_dispatch` runs on the hosted runner over `act`
  (won't reliably emulate `setup-chrome` + real outbound requests to `salaooval.com.br`).

## Open questions for the next session
- ~~Exact `apache-airflow` version to pin...~~ **Resolved 2026-08-27**: `3.3.1`, zero
  conflict with `pandas`/`numpy`/`scikit-learn`. See Phase 1.5 above.
- ~~Whether team scraping gets wired into the same incremental pipeline now...~~
  **Resolved 2026-08-27**: yes, per Victor's direction — see Phase 1.5 above.
- ~~Confirm cron cadence...~~ **Resolved 2026-08-28**: weekly, Monday 06:00 UTC — per
  Victor's direction, matches this doc's original Phase 3 suggestion. See Phase 3 below.
- Confirm `main` is really the intended production/deploy-triggering branch (current
  working branch is `create-data-pipeline`; `main` is the repo's documented default) —
  still open, needed for Phase 4, and now also for restoring Phase 3's `schedule:` cron
  on `main` once `create-data-pipeline` merges for real (see that section's note).
- ~~Get Victor's go-ahead to actually push and run Phase 3's workflow via
  `workflow_dispatch`~~ **Resolved 2026-08-29**: done, validated end-to-end with real
  runs, three bugs found and fixed. See Phase 3's real-validation writeup above.

## Critical files (once implementation starts)
- `src/pipeline/tasks.py`, `src/pipeline/update_games.py` — games task functions + CLI
- `src/pipeline/team_tasks.py`, `src/pipeline/update_teams.py` (new, 2026-08-27) —
  team task functions + CLI, same convention as the games side
- `dags/update_fabr_data_dag.py` (new, 2026-08-27) — Airflow DAG wrapping both
  `tasks.py` and `team_tasks.py`'s functions, two branches converging at
  `check_unresolved_teams`
- `src/scrapping/scrape_games/get_urls.py` — add `filter_urls_by_year`
- `src/utils/team_aliases.py` — consolidated alias source of truth; also documents,
  in a trailing comment block, the cross-slug merges that were checked and rejected —
  read it before adding a new alias, not just before reading the dict; also now home
  to `extract_team_slug()`, shared by `audit_team_aliases.py` and `team_tasks.py`
- `src/pipeline/audit_team_aliases.py` (new, 2026-08-26) — re-runnable slug-based
  audit for finding new team-name splits; run before trusting name resolution after
  any future re-scrape
- `src/utils/utils.py::get_dominant_color` (fixed 2026-08-27) — now excludes near-black
  pixels (not just near-white) and weights k-means cluster choice by saturation, with a
  fallback for genuinely monochrome-black logos; `src/pipeline/recompute_team_colors.py`
  (new) re-applies it to already-scraped teams without a full re-scrape
- `backend/app/seed.py` (done, 2026-08-28) — `sync_from_csv` replaces `seed_if_empty`;
  upserts teams/games, auto-creates placeholder teams for unresolved names
- `backend/app/models.py` (done, 2026-08-28) — `Game.__table_args__`'s
  `uq_game_identity` composite unique constraint
- `backend/app/main.py` (done, 2026-08-28) — `lifespan` runs `alembic upgrade head`
  then `sync_from_csv` unconditionally, every startup
- `backend/alembic/`, `backend/alembic.ini` (new, 2026-08-28) — migration source of
  truth for the schema; `env.py` reads the DB URL from `app.config.settings`, never
  hardcoded; must ship in the Docker image (`backend/Dockerfile` `COPY`s both)
- `backend/tests/conftest.py`, `backend/tests/test_seed.py` (done, 2026-08-28) — swapped
  to `sync_from_csv`; new upsert/placeholder/idempotency test cases
- `.github/workflows/scrape-and-pr.yml` (written, 2026-08-28, **not yet validated with
  a real run** — see Phase 3's progress note); `.github/workflows/deploy.yml` (new,
  Phase 4, not started)
- `backend/fly.toml`, `frontend/fly.toml` (new)
- `.gitignore` — allowlists `data/raw/games/*.csv` and (2026-08-27) `data/raw/teams/*.csv`
