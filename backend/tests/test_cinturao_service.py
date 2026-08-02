import datetime

from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services.cinturao import get_current_champion


def _team(db: Session, name: str) -> Team:
    team = Team(name=name)
    db.add(team)
    db.flush()
    return team


def test_get_current_champion_none_without_games(db_session: Session) -> None:
    assert get_current_champion(db_session) is None


def test_get_current_champion_tracks_latest_winner(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")

    db_session.add(
        Game(
            date=datetime.datetime(2020, 1, 1),
            home_team_id=team_a.id,
            away_team_id=team_b.id,
            winner_team_id=team_a.id,
            defender_team_id=None,
        )
    )
    db_session.add(
        Game(
            date=datetime.datetime(2021, 1, 1),
            home_team_id=team_b.id,
            away_team_id=team_a.id,
            winner_team_id=team_b.id,
            defender_team_id=team_a.id,
        )
    )
    db_session.commit()

    champion, reign_start = get_current_champion(db_session)

    assert champion.name == "Team B"
    assert reign_start == datetime.datetime(2021, 1, 1)


def test_get_current_champion_reign_survives_defenses(db_session: Session) -> None:
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
                date=datetime.datetime(2020, 6, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
            Game(
                date=datetime.datetime(2021, 1, 1),
                home_team_id=team_a.id,
                away_team_id=team_b.id,
                winner_team_id=team_a.id,
                defender_team_id=team_a.id,
            ),
        ]
    )
    db_session.commit()

    champion, reign_start = get_current_champion(db_session)

    assert champion.name == "Team A"
    assert reign_start == datetime.datetime(2020, 1, 1)
