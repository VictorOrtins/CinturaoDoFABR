import datetime

from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services import stats


def _team(db: Session, name: str) -> Team:
    team = Team(name=name)
    db.add(team)
    db.flush()
    return team


def _by_team(entries: list[stats.LeaderboardEntry]) -> dict[str, int]:
    return {entry.team.name: entry.value for entry in entries}


def test_title_defenses_empty_without_games(db_session: Session) -> None:
    assert stats.get_title_defenses(db_session) == []


def test_title_defenses_counts_defender_appearances(db_session: Session) -> None:
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

    result = stats.get_title_defenses(db_session)

    assert len(result) == 1
    assert result[0].team.name == "Team A"
    assert result[0].value == 2


def test_title_wins_counts_title_captures_not_defenses(db_session: Session) -> None:
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

    result = _by_team(stats.get_title_wins(db_session))

    assert result == {"Team A": 1, "Team C": 1}


def test_most_games_played_counts_home_and_away(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    team_c = _team(db_session, "Team C")
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
                away_team_id=team_c.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    result = _by_team(stats.get_most_games_played(db_session))

    assert result == {"Team A": 2, "Team B": 1, "Team C": 1}


def test_most_game_losses_counts_raw_match_losses(db_session: Session) -> None:
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
                home_team_id=team_b.id,
                away_team_id=team_a.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    result = stats.get_most_game_losses(db_session)

    assert len(result) == 1
    assert result[0].team.name == "Team B"
    assert result[0].value == 2


def test_title_losses_counts_belt_losses(db_session: Session) -> None:
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
                winner_team_id=team_c.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    result = stats.get_title_losses(db_session)

    assert len(result) == 1
    assert result[0].team.name == "Team A"
    assert result[0].value == 1


def _reign_change_games(db: Session, team_a: Team, team_b: Team, team_c: Team) -> None:
    db.add_all(
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
                away_team_id=team_c.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
            Game(
                date=datetime.datetime(2020, 1, 31),
                home_team_id=team_a.id,
                away_team_id=team_c.id,
                winner_team_id=team_c.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db.commit()


def test_days_with_title_sums_reign_lengths(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    team_c = _team(db_session, "Team C")
    _reign_change_games(db_session, team_a, team_b, team_c)

    now = datetime.datetime(2020, 2, 10)
    result = _by_team(stats.get_days_with_title(db_session, now=now))

    assert result == {"Team A": 30, "Team C": 10}


def test_longest_reign_tracks_max_single_reign(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    team_c = _team(db_session, "Team C")
    _reign_change_games(db_session, team_a, team_b, team_c)

    now = datetime.datetime(2020, 2, 10)
    result = _by_team(stats.get_longest_reign(db_session, now=now))

    assert result == {"Team A": 30, "Team C": 10}


def test_longest_win_streak_tracks_consecutive_wins(db_session: Session) -> None:
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
            Game(
                date=datetime.datetime(2020, 1, 31),
                home_team_id=team_a.id,
                away_team_id=team_c.id,
                winner_team_id=team_c.id,
                defender_team_id=team_c.id,
            ),
            Game(
                date=datetime.datetime(2020, 2, 10),
                home_team_id=team_a.id,
                away_team_id=team_c.id,
                winner_team_id=team_c.id,
                defender_team_id=team_c.id,
            ),
        ]
    )
    db_session.commit()

    result = _by_team(stats.get_longest_win_streak(db_session))

    assert result == {"Team C": 3, "Team A": 2}


def test_reign_timeline_lists_periods_chronologically(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    team_c = _team(db_session, "Team C")
    _reign_change_games(db_session, team_a, team_b, team_c)

    now = datetime.datetime(2020, 2, 10)
    timeline = stats.get_reign_timeline(db_session, now=now)

    assert [entry.team.name for entry in timeline] == ["Team A", "Team C"]
    assert timeline[0].start == datetime.datetime(2020, 1, 1)
    assert timeline[0].end == datetime.datetime(2020, 1, 31)
    assert timeline[0].ongoing is False
    assert timeline[1].start == datetime.datetime(2020, 1, 31)
    assert timeline[1].end == now
    assert timeline[1].ongoing is True


def test_titles_by_region_groups_by_winner_region(db_session: Session) -> None:
    team_a = Team(name="Team A", region="sul")
    team_b = Team(name="Team B", region="sudeste")
    team_c = Team(name="Team C", region=None)
    db_session.add_all([team_a, team_b, team_c])
    db_session.flush()
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
                away_team_id=team_c.id,
                winner_team_id=team_c.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    entries = stats.get_titles_by_region(db_session)
    result = {entry.region: entry.value for entry in entries}

    assert result == {"sul": 1, "Não informado": 1}


def test_games_per_year_counts_chronologically(db_session: Session) -> None:
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
            Game(
                date=datetime.datetime(2020, 3, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
            Game(
                date=datetime.datetime(2020, 9, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_b.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    result = stats.get_games_per_year(db_session)

    assert [(entry.year, entry.value) for entry in result] == [(2019, 1), (2020, 2)]


def test_score_margin_distribution_buckets_games(db_session: Session) -> None:
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
                home_score=30,
                away_score=0,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
            Game(
                date=datetime.datetime(2020, 1, 21),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                home_score=None,
                away_score=None,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    entries = stats.get_score_margin_distribution(db_session)
    result = {entry.bucket: entry.value for entry in entries}

    assert result == {"1-5": 1, "6-10": 0, "11-15": 0, "16-20": 0, "21+": 1}
