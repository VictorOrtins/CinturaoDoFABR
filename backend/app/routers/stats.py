from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    LeaderboardEntryOut,
    MarginBucketCountOut,
    RegionCountOut,
    ReignTimelineEntryOut,
    YearCountOut,
)
from app.services import stats as stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _out(entries: list[stats_service.LeaderboardEntry]) -> list[LeaderboardEntryOut]:
    return [LeaderboardEntryOut.model_validate(entry) for entry in entries]


@router.get("/title-defenses", response_model=list[LeaderboardEntryOut])
def get_title_defenses(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_title_defenses(db))


@router.get("/title-wins", response_model=list[LeaderboardEntryOut])
def get_title_wins(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_title_wins(db))


@router.get("/most-games", response_model=list[LeaderboardEntryOut])
def get_most_games_played(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_most_games_played(db))


@router.get("/most-losses", response_model=list[LeaderboardEntryOut])
def get_most_game_losses(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_most_game_losses(db))


@router.get("/title-losses", response_model=list[LeaderboardEntryOut])
def get_title_losses(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_title_losses(db))


@router.get("/days-with-title", response_model=list[LeaderboardEntryOut])
def get_days_with_title(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_days_with_title(db))


@router.get("/longest-reign", response_model=list[LeaderboardEntryOut])
def get_longest_reign(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_longest_reign(db))


@router.get("/longest-win-streak", response_model=list[LeaderboardEntryOut])
def get_longest_win_streak(db: Session = Depends(get_db)) -> list[LeaderboardEntryOut]:
    return _out(stats_service.get_longest_win_streak(db))


@router.get("/reign-timeline", response_model=list[ReignTimelineEntryOut])
def get_reign_timeline(db: Session = Depends(get_db)) -> list[ReignTimelineEntryOut]:
    return [
        ReignTimelineEntryOut.model_validate(entry)
        for entry in stats_service.get_reign_timeline(db)
    ]


@router.get("/titles-by-region", response_model=list[RegionCountOut])
def get_titles_by_region(db: Session = Depends(get_db)) -> list[RegionCountOut]:
    entries = stats_service.get_titles_by_region(db)
    return [RegionCountOut.model_validate(entry) for entry in entries]


@router.get("/games-per-year", response_model=list[YearCountOut])
def get_games_per_year(db: Session = Depends(get_db)) -> list[YearCountOut]:
    entries = stats_service.get_games_per_year(db)
    return [YearCountOut.model_validate(entry) for entry in entries]


@router.get("/score-margin-distribution", response_model=list[MarginBucketCountOut])
def get_score_margin_distribution(
    db: Session = Depends(get_db),
) -> list[MarginBucketCountOut]:
    entries = stats_service.get_score_margin_distribution(db)
    return [MarginBucketCountOut.model_validate(entry) for entry in entries]
