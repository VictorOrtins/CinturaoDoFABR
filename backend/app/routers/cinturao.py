from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CurrentChampionOut, TeamOut
from app.services import cinturao as cinturao_service

router = APIRouter(prefix="/api/cinturao", tags=["cinturao"])


@router.get("/current", response_model=CurrentChampionOut)
def get_current_champion(db: Session = Depends(get_db)) -> CurrentChampionOut:
    result = cinturao_service.get_current_champion(db)
    if result is None:
        raise HTTPException(status_code=404, detail="No title games recorded yet")
    team, champion_since = result
    return CurrentChampionOut(
        team=TeamOut.model_validate(team), champion_since=champion_since
    )
