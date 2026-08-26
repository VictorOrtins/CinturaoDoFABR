import pandas as pd

from src.pipeline import tasks

GAMES_COLUMNS = ["Data", "Mandante", "Hor/Res", "Visitante", "Campo", "Torneio"]


class TestMergeAndPreprocess:
    def test_merges_dedupes_and_applies_aliases(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        output_dir = tmp_path / "processed"

        historical = pd.DataFrame(
            [
                {
                    "Data": "2020-01-01 14:00:00",
                    "Mandante": "Galo FA",
                    "Hor/Res": "10 - 07",
                    "Visitante": "Time B",
                    "Campo": None,
                    "Torneio": "bfa-2020",
                },
            ],
            columns=GAMES_COLUMNS,
        )
        historical.to_csv(raw_dir / "games_historical.csv", index=False)

        delta = pd.DataFrame(
            [
                # Exact duplicate of the historical game (same scraped values) -> no-op.
                {
                    "Data": "2020-01-01 14:00:00",
                    "Mandante": "Galo FA",
                    "Hor/Res": "10 - 07",
                    "Visitante": "Time B",
                    "Campo": None,
                    "Torneio": "bfa-2020",
                },
                # A genuinely new game.
                {
                    "Data": "2021-01-01 14:00:00",
                    "Mandante": "Time B",
                    "Hor/Res": "14 - 21",
                    "Visitante": "Galo FA",
                    "Campo": None,
                    "Torneio": "bfa-2021",
                },
            ],
            columns=GAMES_COLUMNS,
        )
        delta.to_csv(raw_dir / "games_delta.csv", index=False)

        output_path = tasks.merge_and_preprocess(raw_dir=raw_dir, output_dir=output_dir)

        result_df = pd.read_csv(output_path)

        assert len(result_df) == 2
        assert set(result_df["Mandante"]) | set(result_df["Visitante"]) == {"Galo FA", "Time B"}


class TestCheckUnresolvedTeams:
    def test_reports_names_not_in_the_team_directory(self, tmp_path):
        games_path = tmp_path / "games.csv"
        teams_path = tmp_path / "teams.csv"
        output_path = tmp_path / "unresolved_teams.txt"

        pd.DataFrame(
            [
                {"Mandante": "Known Team", "Visitante": "Unknown Team FA"},
            ]
        ).to_csv(games_path, index=False)

        pd.DataFrame([{"Nome": "Known Team"}]).to_csv(teams_path, index=False)

        result_path = tasks.check_unresolved_teams(
            games_path=games_path, teams_path=teams_path, output_path=output_path
        )

        assert result_path == output_path
        assert output_path.read_text().strip() == "Unknown Team FA"

    def test_writes_empty_file_when_every_team_resolves(self, tmp_path):
        games_path = tmp_path / "games.csv"
        teams_path = tmp_path / "teams.csv"
        output_path = tmp_path / "unresolved_teams.txt"

        pd.DataFrame([{"Mandante": "Known Team", "Visitante": "Known Team"}]).to_csv(games_path, index=False)
        pd.DataFrame([{"Nome": "Known Team"}]).to_csv(teams_path, index=False)

        tasks.check_unresolved_teams(games_path=games_path, teams_path=teams_path, output_path=output_path)

        assert output_path.read_text() == ""
