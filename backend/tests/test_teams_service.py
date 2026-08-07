import datetime

from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services import teams


def _team(db: Session, name: str) -> Team:
    team = Team(name=name)
    db.add(team)
    db.flush()
    return team


def test_list_teams_returns_all_by_default(db_session: Session) -> None:
    _team(db_session, "Team A")
    _team(db_session, "Team B")
    db_session.commit()

    result = teams.list_teams(db_session)

    assert {team.name for team in result} == {"Team A", "Team B"}


def test_list_teams_played_only_excludes_unplayed(db_session: Session) -> None:
    team_a = _team(db_session, "Team A")
    team_b = _team(db_session, "Team B")
    _team(db_session, "Team C (never played)")
    db_session.add(
        Game(
            date=datetime.datetime(2020, 1, 1),
            home_team_id=team_a.id,
            away_team_id=team_b.id,
            winner_team_id=team_a.id,
            defender_team_id=None,
        )
    )
    db_session.commit()

    result = teams.list_teams(db_session, played_only=True)

    assert {team.name for team in result} == {"Team A", "Team B"}
