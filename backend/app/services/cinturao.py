import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Game, Team


def get_current_champion(db: Session) -> tuple[Team, datetime.datetime] | None:
    """Current title holder, and the date their current (unbroken) reign started."""
    games = (
        db.query(Game)
        .options(joinedload(Game.winner_team))
        .order_by(Game.date.asc(), Game.id.asc())
        .all()
    )
    if not games:
        return None

    reign_start = games[0].date
    champion_id = games[0].winner_team_id
    for game in games[1:]:
        if game.winner_team_id != champion_id:
            champion_id = game.winner_team_id
            reign_start = game.date

    champion = games[-1].winner_team
    assert champion is not None, "every title game must have a winner"
    return champion, reign_start
