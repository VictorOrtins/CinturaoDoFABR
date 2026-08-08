import datetime

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services import query_engine as qe


def _team(
    db: Session, name: str, region: str | None = None, state: str | None = None
) -> Team:
    team = Team(name=name, region=region, state=state)
    db.add(team)
    db.flush()
    return team


def _by_label(result: qe.QueryResult) -> dict[str, float]:
    return {bucket.label: bucket.value for bucket in result.buckets}


def test_group_by_team_requires_team_role() -> None:
    with pytest.raises(ValidationError):
        qe.QuerySpec(group_by=qe.Dimension.TEAM)


def test_count_requires_games_metric() -> None:
    with pytest.raises(ValidationError):
        qe.QuerySpec(
            group_by=qe.Dimension.YEAR,
            metric_field=qe.MetricField.SCORE_MARGIN,
            aggregation=qe.AggregationFunction.COUNT,
        )


def test_sum_requires_numeric_metric() -> None:
    with pytest.raises(ValidationError):
        qe.QuerySpec(group_by=qe.Dimension.YEAR, aggregation=qe.AggregationFunction.SUM)


def test_points_scored_requires_team_role() -> None:
    with pytest.raises(ValidationError):
        qe.QuerySpec(
            group_by=qe.Dimension.YEAR,
            metric_field=qe.MetricField.POINTS_SCORED,
            aggregation=qe.AggregationFunction.SUM,
        )


def test_defender_role_matches_title_defenses(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
            Game(
                date=datetime.datetime(2020, 1, 11),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
            Game(
                date=datetime.datetime(2020, 1, 21),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(group_by=qe.Dimension.TEAM, team_role=qe.TeamRole.DEFENDER)
    result = qe.execute(db_session, spec)

    assert result.chart_type == "leaderboard"
    assert _by_label(result) == {"Team A": 2}
    assert result.buckets[0].team is not None
    assert result.buckets[0].team.name == "Team A"


def test_winner_with_belt_changed_hands_matches_title_wins(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_c = _team(db_session, "Team C")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_c.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
            Game(
                date=datetime.datetime(2020, 1, 11),
                home_team_id=team_a.id,
                away_team_id=team_c.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
            Game(
                date=datetime.datetime(2020, 1, 21),
                home_team_id=team_a.id,
                away_team_id=team_c.id,
                winner_team_id=team_c.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.TEAM,
        team_role=qe.TeamRole.WINNER,
        outcome_filter=qe.OutcomeFilter.BELT_CHANGED_HANDS,
    )
    result = qe.execute(db_session, spec)

    assert _by_label(result) == {"Team A": 1, "Team C": 1}


def test_games_per_year_filtered_by_state(db_session: Session) -> None:
    team_a = _team(db_session, "Team A", state="RS")
    team_b = _team(db_session, "Team B", state="SP")
    team_c = _team(db_session, "Team C", state="SP")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2019, 6, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
            Game(
                date=datetime.datetime(2020, 3, 1),
                home_team_id=team_b.id,
                away_team_id=team_c.id,
                winner_team_id=team_b.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.YEAR,
        team_role=qe.TeamRole.PARTICIPANT,
        filters=qe.FilterSpec(state="RS"),
    )
    result = qe.execute(db_session, spec)

    assert result.chart_type == "line"
    assert _by_label(result) == {"2019": 1}


def test_participant_does_not_double_count_games_per_year(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2019, 6, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(group_by=qe.Dimension.YEAR, team_role=qe.TeamRole.PARTICIPANT)
    result = qe.execute(db_session, spec)

    assert _by_label(result) == {"2019": 1}


def test_participant_does_not_double_count_same_region_matchup(
    db_session: Session,
) -> None:
    team_a = _team(db_session, "Team A", region="sul")
    team_b = _team(db_session, "Team B", region="sul")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(group_by=qe.Dimension.REGION, team_role=qe.TeamRole.PARTICIPANT)
    result = qe.execute(db_session, spec)

    assert _by_label(result) == {"sul": 1}


def test_region_dimension_buckets_and_labels(db_session: Session) -> None:
    team_a = _team(db_session, "Team A", region="sul")
    team_b = _team(db_session, "Team B", region="sudeste")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(group_by=qe.Dimension.REGION, team_role=qe.TeamRole.PARTICIPANT)
    result = qe.execute(db_session, spec)

    assert result.chart_type == "bar"
    assert _by_label(result) == {"sul": 1, "sudeste": 1}


def test_avg_score_margin_by_team(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                home_score=20,
                away_score=10,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
            Game(
                date=datetime.datetime(2020, 1, 11),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                home_score=30,
                away_score=20,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.TEAM,
        team_role=qe.TeamRole.PARTICIPANT,
        metric_field=qe.MetricField.SCORE_MARGIN,
        aggregation=qe.AggregationFunction.AVG,
    )
    result = qe.execute(db_session, spec)

    assert _by_label(result) == {"Team A": 10.0, "Team B": 10.0}


def test_max_score_margin_by_winner(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                home_score=20,
                away_score=17,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
            Game(
                date=datetime.datetime(2020, 1, 11),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                home_score=40,
                away_score=10,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.TEAM,
        team_role=qe.TeamRole.WINNER,
        metric_field=qe.MetricField.SCORE_MARGIN,
        aggregation=qe.AggregationFunction.MAX,
    )
    result = qe.execute(db_session, spec)

    assert _by_label(result) == {"Team A": 30.0}


def test_unknown_team_name_raises(db_session: Session) -> None:
    _team(db_session, "Team A")
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.TEAM,
        team_role=qe.TeamRole.PARTICIPANT,
        filters=qe.FilterSpec(team_name="Totally Unknown Team Xyz"),
    )
    with pytest.raises(qe.QueryEngineError):
        qe.execute(db_session, spec)


def test_unknown_region_raises(db_session: Session) -> None:
    _team(db_session, "Team A", region="sul")
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.TEAM,
        team_role=qe.TeamRole.PARTICIPANT,
        filters=qe.FilterSpec(region="not-a-real-region"),
    )
    with pytest.raises(qe.QueryEngineError):
        qe.execute(db_session, spec)


def test_no_matching_games_returns_empty_buckets(db_session: Session) -> None:
    team_a = _team(db_session, "Team A", region="sul")
    team_b = _team(db_session, "Team B", region="sul")
    _team(db_session, "Team C", region="sudeste")  # exists, but plays no games
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
        ]
    )
    db_session.commit()

    spec = qe.QuerySpec(
        group_by=qe.Dimension.TEAM,
        team_role=qe.TeamRole.PARTICIPANT,
        filters=qe.FilterSpec(region="sudeste"),
    )
    result = qe.execute(db_session, spec)

    assert result.buckets == []


def test_limit_caps_team_leaderboard(db_session: Session) -> None:
    teams = [_team(db_session, f"Team {i}") for i in range(15)]
    games = []
    for i, team in enumerate(teams):
        opponent = teams[(i + 1) % len(teams)]
        for _ in range(i + 1):
            games.append(
                Game(
                    date=datetime.datetime(2020, 1, 1) + datetime.timedelta(days=i),
                    home_team_id=team.id,
                    away_team_id=opponent.id,
                    winner_team_id=team.id,
                    defender_team_id=None,
                )
            )
    db_session.add_all(games)
    db_session.commit()

    spec = qe.QuerySpec(group_by=qe.Dimension.TEAM, team_role=qe.TeamRole.WINNER)
    result = qe.execute(db_session, spec)

    assert len(result.buckets) == qe.TOP_N
    values = [bucket.value for bucket in result.buckets]
    assert values == sorted(values, reverse=True)


def test_table_games_filtered_by_team_name(db_session: Session) -> None:
    team_a = _team(db_session, "Espectros")
    team_b = _team(db_session, "Team B")
    team_c = _team(db_session, "Team C")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                home_score=20,
                away_score=17,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
            Game(
                date=datetime.datetime(2020, 2, 1),
                home_team_id=team_b.id,
                away_team_id=team_c.id,
                winner_team_id=team_b.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    spec = qe.TableSpec(
        entity=qe.TableEntity.GAMES, filters=qe.FilterSpec(team_name="Espectros")
    )
    result = qe.execute_table(db_session, spec)

    assert result.columns == ["Data", "Mandante", "Visitante", "Placar", "Campeão"]
    assert len(result.rows) == 1
    assert result.rows[0] == {
        "Data": "2020-01-01",
        "Mandante": "Espectros",
        "Visitante": "Team B",
        "Placar": "20 x 17",
        "Campeão": "Espectros",
    }


def test_table_games_missing_score_shows_dash(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    db_session.add_all(
        [
            Game(
                date=datetime.datetime(2020, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=None,
            ),
        ]
    )
    db_session.commit()

    spec = qe.TableSpec(entity=qe.TableEntity.GAMES)
    result = qe.execute_table(db_session, spec)

    assert result.rows[0]["Placar"] == "-"


def test_table_teams_filtered_by_state(db_session: Session) -> None:
    _team(db_session, "Team A", state="SP")
    _team(db_session, "Team B", state="SP")
    _team(db_session, "Team C", state="RJ")
    db_session.commit()

    spec = qe.TableSpec(entity=qe.TableEntity.TEAMS, filters=qe.FilterSpec(state="SP"))
    result = qe.execute_table(db_session, spec)

    assert result.columns == ["Time", "Cidade", "Estado", "Região"]
    assert {row["Time"] for row in result.rows} == {"Team A", "Team B"}


def test_table_respects_limit(db_session: Session) -> None:
    for i in range(5):
        _team(db_session, f"Team {i}")
    db_session.commit()

    spec = qe.TableSpec(entity=qe.TableEntity.TEAMS, limit=2)
    result = qe.execute_table(db_session, spec)

    assert len(result.rows) == 2
