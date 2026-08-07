from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GameOut, TeamOut
from app.services import games as games_service
from app.services import teams as teams_service

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(played: bool = False, db: Session = Depends(get_db)) -> list[TeamOut]:
    teams = teams_service.list_teams(db, played_only=played)
    return [TeamOut.model_validate(team) for team in teams]


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)) -> TeamOut:
    team = teams_service.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamOut.model_validate(team)


@router.get("/{team_id}/games", response_model=list[GameOut])
def list_team_games(team_id: int, db: Session = Depends(get_db)) -> list[GameOut]:
    if teams_service.get_team(db, team_id) is None:
        raise HTTPException(status_code=404, detail="Team not found")
    games = games_service.list_games_for_team(db, team_id)
    return [GameOut.model_validate(game) for game in games]
