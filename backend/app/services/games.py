from sqlalchemy import or_
from sqlalchemy.orm import Query, Session, joinedload

from app.models import Game


def _games_query(db: Session) -> Query[Game]:
    return db.query(Game).options(
        joinedload(Game.home_team),
        joinedload(Game.away_team),
        joinedload(Game.winner_team),
        joinedload(Game.defender_team),
    )


def list_games(db: Session) -> list[Game]:
    return _games_query(db).order_by(Game.date.asc(), Game.id.asc()).all()


def list_games_for_team(db: Session, team_id: int) -> list[Game]:
    return (
        _games_query(db)
        .filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))
        .order_by(Game.date.asc(), Game.id.asc())
        .all()
    )
