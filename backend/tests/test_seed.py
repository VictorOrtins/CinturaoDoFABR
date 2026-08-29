import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Game, Team
from app.seed import sync_from_csv

TEAMS_HEADER = [
    "Nome",
    "URL da Imagem",
    "Sede",
    "Cor Primária",
    "URL",
    "Estado",
    "Regiao",
]
GAMES_HEADER = [
    "Data",
    "Mandante",
    "Visitante",
    "Campo",
    "Torneio",
    "Fase",
    "Pontos Mandante",
    "Pontos Visitante",
    "Vencedor",
    "Defensor do Título",
]


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _write_seed_dir(tmp_path: Path, games_rows: list[dict[str, str]]) -> Path:
    seed_dir = tmp_path / "seed_data"
    seed_dir.mkdir()
    _write_csv(
        seed_dir / "teams.csv",
        TEAMS_HEADER,
        [
            {"Nome": "Home FA", "Estado": "SP", "Regiao": "Sudeste"},
            {"Nome": "Away FA", "Estado": "RJ", "Regiao": "Sudeste"},
        ],
    )
    _write_csv(seed_dir / "games.csv", GAMES_HEADER, games_rows)
    return seed_dir


def _game_row(
    date: str = "2020-01-01 15:00:00",
    home: str = "Home FA",
    away: str = "Away FA",
    tournament: str = "Torneio Teste",
    home_score: str = "10",
    away_score: str = "7",
) -> dict[str, str]:
    return {
        "Data": date,
        "Mandante": home,
        "Visitante": away,
        "Campo": "Estádio Teste",
        "Torneio": tournament,
        "Fase": "Final",
        "Pontos Mandante": home_score,
        "Pontos Visitante": away_score,
        "Vencedor": home,
        "Defensor do Título": home,
    }


def test_sync_populates_teams_and_games(seeded_db_session: Session) -> None:
    assert seeded_db_session.query(Team).count() > 0
    assert seeded_db_session.query(Game).count() > 0


def test_sync_never_drops_a_game_for_an_unresolved_team_name(
    seeded_db_session: Session,
) -> None:
    """Every row in games.csv now produces a Game - an unresolved team name
    creates a placeholder Team instead of skipping the game (replaces the old
    skip-count lock-in test, which existed to guard the opposite behavior)."""
    with (settings.seed_data_dir / "games.csv").open(encoding="utf-8") as f:
        total_rows = sum(1 for _ in csv.DictReader(f))

    assert seeded_db_session.query(Game).count() == total_rows


def test_sync_creates_placeholder_team_for_unresolved_name(
    db_session: Session, tmp_path: Path
) -> None:
    seed_dir = _write_seed_dir(
        tmp_path, [_game_row(home="Unknown Rovers", away="Away FA")]
    )

    sync_from_csv(db_session, seed_dir)

    assert db_session.query(Game).count() == 1
    placeholder = db_session.query(Team).filter(Team.name == "Unknown Rovers").one()
    assert placeholder.state is None


def test_sync_is_idempotent(seeded_db_session: Session) -> None:
    team_count = seeded_db_session.query(Team).count()
    game_count = seeded_db_session.query(Game).count()

    sync_from_csv(seeded_db_session, settings.seed_data_dir)

    assert seeded_db_session.query(Team).count() == team_count
    assert seeded_db_session.query(Game).count() == game_count


def test_sync_inserts_only_the_new_game_on_a_second_run(
    db_session: Session, tmp_path: Path
) -> None:
    seed_dir = _write_seed_dir(tmp_path, [_game_row()])
    sync_from_csv(db_session, seed_dir)
    assert db_session.query(Game).count() == 1

    _write_csv(
        seed_dir / "games.csv",
        GAMES_HEADER,
        [_game_row(), _game_row(date="2020-01-08 15:00:00")],
    )
    sync_from_csv(db_session, seed_dir)

    assert db_session.query(Game).count() == 2


def test_sync_updates_score_in_place_instead_of_duplicating(
    db_session: Session, tmp_path: Path
) -> None:
    seed_dir = _write_seed_dir(tmp_path, [_game_row(home_score="10", away_score="7")])
    sync_from_csv(db_session, seed_dir)

    _write_csv(
        seed_dir / "games.csv",
        GAMES_HEADER,
        [_game_row(home_score="14", away_score="7")],
    )
    sync_from_csv(db_session, seed_dir)

    assert db_session.query(Game).count() == 1
    game = db_session.query(Game).one()
    assert game.home_score == 14


def test_games_reference_valid_teams(seeded_db_session: Session) -> None:
    games = seeded_db_session.query(Game).all()
    for game in games:
        assert game.home_team is not None
        assert game.away_team is not None
