from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TeamOut
from app.services import teams as teams_service

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db)) -> list[TeamOut]:
    return [TeamOut.model_validate(team) for team in teams_service.list_teams(db)]


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)) -> TeamOut:
    team = teams_service.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamOut.model_validate(team)
