# Data pipeline: scrape → DB → deploy (handoff doc)

**Status**: Phase 0 done (2026-08-23). **Phase 1 is done** (2026-08-24 through
2026-08-26, branch `create-data-pipeline`) — task functions and CLI are built, the
bootstrap crawl is complete (all 208 live tournaments), the systematic team-name-alias
audit flagged as an open question on 2026-08-24 is done (28 splits found via a new
URL-slug-based method, 25 applied after review, 6 human-proposed merges checked and
correctly rejected — see "Team name slug audit (2026-08-26)"), and — the item that used
to be "what's actually left" — **both real seed CSVs have been regenerated for the
first time this phase**: `backend/seed_data/games.csv` (165→178 rows) and `teams.csv`
(182→386 rows, plus 5 more aliases found in the process), reconciled and verified (see
"Backend regeneration (2026-08-26)" at the end of that same section). The known
team-resolution gap in `CLAUDE.MD` dropped from 20/165 to 4/178. Both test suites green.
Nothing from this session is committed yet — `git status` on `create-data-pipeline`
shows the real diff; deciding what to commit is the next actual decision. Phases 1.5-5
still not started — no Airflow, no Fly.io app, no CI/CD. This is everything a future
session needs to pick this up cold.

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

### Phase 1.5 — Airflow DAG
- New `dags/update_games_dag.py` — a real Airflow DAG: `PythonOperator` per task from
  `src/pipeline/tasks.py`, explicit `>>` dependency chain, `retries=2` with backoff on
  the scrape task (network flakiness against a live third-party site), a final task
  that surfaces `check_unresolved_teams()`'s output for the PR-body step.
- Pin an exact `apache-airflow` version + matching constraints file. Verify the
  dependency-conflict risk described above in a scratch venv before wiring into CI.
- Local dev loop: `airflow dags test update_games <date>` runs it without any
  scheduler/webserver — this is also how you'll manually test it before trusting the
  CI job.

### Phase 2 — Backend DB sync (replace seed-once with real sync)
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

### Phase 3 — GitHub Actions: scheduled scrape + PR
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

### Phase 4 — Fly.io deployment
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
- Exact `apache-airflow` version to pin, and whether its dependency constraints
  conflict with `requirements.txt`'s existing pins (`pandas`, `numpy`, `scikit-learn`)
  — check this **first**, before writing any DAG code, since it could force isolating
  Airflow into its own install step.
- Confirm cron cadence (weekly vs. some other interval) and exact day/time.
- Whether team scraping (`src/scrapping/scrape_teams/`) gets wired into the same
  incremental pipeline now, or stays out of scope for this first pass (games-only).
- Confirm `main` is really the intended production/deploy-triggering branch (current
  working branch is `update-design`; `main` is the repo's documented default).

## Critical files (once implementation starts)
- `src/pipeline/tasks.py`, `src/pipeline/update_games.py` (new) — task functions +
  CLI entrypoint
- `dags/update_games_dag.py` (new) — Airflow DAG wrapping the same task functions
- `src/scrapping/scrape_games/get_urls.py` — add `filter_urls_by_year`
- `src/utils/team_aliases.py` — consolidated alias source of truth; also documents,
  in a trailing comment block, the cross-slug merges that were checked and rejected —
  read it before adding a new alias, not just before reading the dict
- `src/pipeline/audit_team_aliases.py` (new, 2026-08-26) — re-runnable slug-based
  audit for finding new team-name splits; run before trusting name resolution after
  any future re-scrape
- `backend/app/seed.py` — replace `seed_if_empty` with `sync_from_csv`
- `backend/app/models.py` — composite unique index on `Game`
- `backend/app/main.py`, `backend/tests/conftest.py` — swap seed call
- `.github/workflows/scrape-and-pr.yml`, `.github/workflows/deploy.yml` (new)
- `backend/fly.toml`, `frontend/fly.toml` (new)
- `.gitignore` — allowlist `data/raw/games/*.csv`
