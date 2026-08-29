import pandas as pd

from src.pipeline import team_tasks


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


class TestReconcileTeamsCsv:
    def test_applies_team_name_aliases(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.preprocessing.teams.preprocessor.TEAM_NAME_ALIASES",
            {"Raw Label": "Canonical Team"},
        )

        raw_path = _write_csv(
            tmp_path / "raw_teams.csv",
            [{"Nome": "Raw Label", "Sede": "São Paulo/SP", "URL": "https://x/times/canonical-slug/"}],
        )

        output_path = team_tasks.reconcile_teams_csv(
            raw_path,
            existing_seed_path=tmp_path / "no_old_file.csv",
            output_path=tmp_path / "result.csv",
        )

        result_df = pd.read_csv(output_path)
        assert list(result_df["Nome"]) == ["Canonical Team"]
        assert result_df.iloc[0]["Estado"] == "SP"

    def test_carries_forward_estado_by_slug_when_sede_is_blank(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.preprocessing.teams.preprocessor.TEAM_NAME_ALIASES", {})

        old_path = _write_csv(
            tmp_path / "old_teams.csv",
            [{"Nome": "Some Team", "URL": "https://x/times/some-team/", "Estado": "RS", "Regiao": "sul"}],
        )
        raw_path = _write_csv(
            tmp_path / "raw_teams.csv",
            [{"Nome": "Some Team", "Sede": None, "URL": "https://x/times/some-team/"}],
        )

        output_path = team_tasks.reconcile_teams_csv(
            raw_path, existing_seed_path=old_path, output_path=tmp_path / "result.csv"
        )

        result_df = pd.read_csv(output_path)
        assert result_df.iloc[0]["Estado"] == "RS"
        assert result_df.iloc[0]["Regiao"] == "sul"

    def test_new_team_without_old_counterpart_keeps_null_estado(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.preprocessing.teams.preprocessor.TEAM_NAME_ALIASES", {})

        old_path = _write_csv(
            tmp_path / "old_teams.csv",
            [{"Nome": "Other Team", "URL": "https://x/times/other-team/", "Estado": "RS", "Regiao": "sul"}],
        )
        raw_path = _write_csv(
            tmp_path / "raw_teams.csv",
            [{"Nome": "Brand New Team", "Sede": None, "URL": "https://x/times/brand-new-team/"}],
        )

        output_path = team_tasks.reconcile_teams_csv(
            raw_path, existing_seed_path=old_path, output_path=tmp_path / "result.csv"
        )

        result_df = pd.read_csv(output_path)
        assert len(result_df) == 1
        assert pd.isna(result_df.iloc[0]["Estado"])

    def test_drops_row_with_blank_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.preprocessing.teams.preprocessor.TEAM_NAME_ALIASES", {})

        raw_path = _write_csv(
            tmp_path / "raw_teams.csv",
            [
                {"Nome": "", "Sede": None, "URL": "https://x/times/blank/"},
                {"Nome": "Valid Team", "Sede": None, "URL": "https://x/times/valid-team/"},
            ],
        )

        output_path = team_tasks.reconcile_teams_csv(
            raw_path,
            existing_seed_path=tmp_path / "no_old_file.csv",
            output_path=tmp_path / "result.csv",
        )

        result_df = pd.read_csv(output_path)
        assert list(result_df["Nome"]) == ["Valid Team"]

    def test_collision_after_alias_keeps_row_with_populated_estado(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.preprocessing.teams.preprocessor.TEAM_NAME_ALIASES",
            {"Raw Label A": "Canonical Team", "Raw Label B": "Canonical Team"},
        )

        old_path = _write_csv(
            tmp_path / "old_teams.csv",
            [{"Nome": "Canonical Team", "URL": "https://x/times/slug-a/", "Estado": "RJ", "Regiao": "sudeste"}],
        )
        raw_path = _write_csv(
            tmp_path / "raw_teams.csv",
            [
                {"Nome": "Raw Label A", "Sede": None, "URL": "https://x/times/slug-a/"},
                {"Nome": "Raw Label B", "Sede": None, "URL": "https://x/times/slug-b/"},
            ],
        )

        output_path = team_tasks.reconcile_teams_csv(
            raw_path, existing_seed_path=old_path, output_path=tmp_path / "result.csv"
        )

        result_df = pd.read_csv(output_path)
        assert len(result_df) == 1
        assert result_df.iloc[0]["Nome"] == "Canonical Team"
        assert result_df.iloc[0]["Estado"] == "RJ"
