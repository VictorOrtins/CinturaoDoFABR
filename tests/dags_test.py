from airflow.models import DagBag


def test_update_fabr_data_dag_has_no_import_errors_and_expected_tasks():
    dagbag = DagBag(dag_folder="dags")

    assert dagbag.import_errors == {}

    dag = dagbag.get_dag("update_fabr_data")
    assert dag is not None
    assert {t.task_id for t in dag.tasks} == {
        "scrape_games",
        "merge_and_preprocess",
        "run_cinturao",
        "regenerate_seed_csv",
        "scrape_teams",
        "reconcile_teams_csv",
        "check_unresolved_teams",
    }
