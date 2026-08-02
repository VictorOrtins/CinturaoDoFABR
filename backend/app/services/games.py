from sqlalchemy.orm import Session, joinedload

from app.models import Game


def list_games(db: Session) -> list[Game]:
    return (
        db.query(Game)
        .options(
            joinedload(Game.home_team),
            joinedload(Game.away_team),
            joinedload(Game.winner_team),
            joinedload(Game.defender_team),
        )
        .order_by(Game.date.asc(), Game.id.asc())
        .all()
    )
