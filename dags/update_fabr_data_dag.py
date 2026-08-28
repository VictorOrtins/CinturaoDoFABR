"""Wraps the plain, orchestrator-agnostic functions in src/pipeline/tasks.py and
src/pipeline/team_tasks.py in a real Airflow DAG. Those modules stay untouched here -
this file is a thin adapter (Path<->str conversion for XCom, retry policy, wiring),
not where the pipeline logic itself lives. See docs/DATA_PIPELINE.md's Phase 1.5
section for the full design rationale (why Airflow, why run via `airflow dags test`
in an ephemeral CI runner instead of a persistent scheduler, why games and teams are
two branches in one DAG rather than a single linear chain).

One-time setup (see requirements-airflow.txt for the exact install command):
    uv pip install --python .venv/bin/python -r requirements-airflow.txt --constraint <url in that file>

Local dev loop (no scheduler/webserver/API-server needed):
    export AIRFLOW_HOME=<repo>/.airflow-home
    export AIRFLOW__CORE__DAGS_FOLDER=<repo>/dags
    airflow db migrate                      # once
    airflow dags reserialize                # registers this DAG in the metadata db
    airflow dags test update_fabr_data <date>
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import Param, dag, get_current_context, task

from src.pipeline import tasks as game_tasks
from src.pipeline import team_tasks


@dag(
    dag_id="update_fabr_data",
    schedule=None,  # recurrence is owned by GitHub Actions' cron (Phase 3), not Airflow's own scheduler
    start_date=datetime(2026, 1, 1),
    catchup=False,
    params={"since_year": Param(default=datetime.now().year - 1, type="integer")},
)
def update_fabr_data() -> None:
    @task(retries=2, retry_delay=timedelta(minutes=2))
    def scrape_games() -> str:
        # Uses the accumulated-file variant, not scrape_recent_games - a recurring
        # run needs storage proportional to genuinely new games found, not to run
        # frequency. See tasks.py::scrape_recent_games_accumulated's docstring.
        since_year = get_current_context()["params"]["since_year"]
        return str(game_tasks.scrape_recent_games_accumulated(since_year=since_year))

    @task
    def merge_and_preprocess(_raw_games_path: str) -> str:
        # _raw_games_path is unused - merge_and_preprocess() reads every file already
        # on disk under RAW_GAMES_DIR, it doesn't take a path argument. It's still
        # threaded through here purely to make the scrape -> merge ordering explicit.
        return str(game_tasks.merge_and_preprocess())

    @task
    def run_cinturao(preprocessed_path: str) -> str:
        return str(game_tasks.run_cinturao(Path(preprocessed_path)))

    @task
    def regenerate_seed_csv(cinturao_path: str) -> None:
        game_tasks.regenerate_seed_csv(Path(cinturao_path))

    @task(retries=2, retry_delay=timedelta(minutes=2))
    def scrape_teams() -> str:
        return str(team_tasks.scrape_teams())

    @task
    def reconcile_teams_csv(raw_teams_path: str) -> None:
        team_tasks.reconcile_teams_csv(Path(raw_teams_path))

    @task
    def check_unresolved_teams() -> str:
        return str(game_tasks.check_unresolved_teams())

    raw_games_path = scrape_games()
    preprocessed_path = merge_and_preprocess(raw_games_path)
    cinturao_path = run_cinturao(preprocessed_path)
    games_done = regenerate_seed_csv(cinturao_path)

    raw_teams_path = scrape_teams()
    teams_done = reconcile_teams_csv(raw_teams_path)

    # check_unresolved_teams() takes no XCom input - it reads the two seed files
    # directly (defaults already point at them). Both upstream tasks return None, and
    # TaskFlow doesn't push a return_value XCom for a None result, so a plain ">>"
    # (structural ordering only) is used here rather than passing their results as
    # unused arguments, which would try to XCom-pull a value that was never pushed.
    unresolved = check_unresolved_teams()
    games_done >> unresolved
    teams_done >> unresolved


update_fabr_data()
