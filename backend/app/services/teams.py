from sqlalchemy.orm import Session

from app.models import Game, Team


def list_teams(db: Session, played_only: bool = False) -> list[Team]:
    query = db.query(Team)
    if played_only:
        # teams.csv is a broader FABR team directory; most teams in it never
        # actually held or contested the belt. Games from either side of the
        # matchup mark a team as having played a title game.
        home_ids = {row[0] for row in db.query(Game.home_team_id).distinct()}
        away_ids = {row[0] for row in db.query(Game.away_team_id).distinct()}
        query = query.filter(Team.id.in_(home_ids | away_ids))
    return query.order_by(Team.name).all()


def get_team(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)
