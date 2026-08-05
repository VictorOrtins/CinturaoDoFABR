import csv

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Game, Team
from app.seed import seed_if_empty


def test_seed_populates_teams_and_games(seeded_db_session: Session) -> None:
    assert seeded_db_session.query(Team).count() > 0
    assert seeded_db_session.query(Game).count() > 0


def test_seed_skip_count_matches_known_team_name_mismatches(
    seeded_db_session: Session,
) -> None:
    """Locks in the current, known count of games skipped because their team names
    don't exactly match teams.csv (see the comment in app/seed.py::_seed_games). If
    this fails, either the seed CSVs changed (update the expected numbers below) or a
    regression silently started dropping more/fewer games than before."""
    with (settings.seed_data_dir / "games.csv").open(encoding="utf-8") as f:
        total_rows = sum(1 for _ in csv.DictReader(f))

    assert total_rows == 165
    assert seeded_db_session.query(Game).count() == 145


def test_seed_is_idempotent(seeded_db_session: Session) -> None:
    team_count = seeded_db_session.query(Team).count()
    game_count = seeded_db_session.query(Game).count()

    seed_if_empty(seeded_db_session)

    assert seeded_db_session.query(Team).count() == team_count
    assert seeded_db_session.query(Game).count() == game_count


def test_games_reference_valid_teams(seeded_db_session: Session) -> None:
    games = seeded_db_session.query(Game).all()
    for game in games:
        assert game.home_team is not None
        assert game.away_team is not None
