from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GameOut
from app.services import games as games_service

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=list[GameOut])
def list_games(db: Session = Depends(get_db)) -> list[GameOut]:
    return [GameOut.model_validate(game) for game in games_service.list_games(db)]
