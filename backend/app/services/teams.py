from sqlalchemy.orm import Session

from app.models import Team


def list_teams(db: Session) -> list[Team]:
    return db.query(Team).order_by(Team.name).all()


def get_team(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)
