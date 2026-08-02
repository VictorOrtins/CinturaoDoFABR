import csv
import datetime
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Game, Team

logger = logging.getLogger(__name__)

GAME_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _seed_teams(db: Session, teams_csv: Path) -> dict[str, int]:
    name_to_id: dict[str, int] = {}
    with teams_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            team = Team(
                name=row["Nome"].strip(),
                logo_url=_clean(row.get("URL da Imagem")),
                home_city=_clean(row.get("Sede")),
                primary_color=_clean(row.get("Cor Primária")),
                external_url=_clean(row.get("URL")),
                state=_clean(row.get("Estado")),
                region=_clean(row.get("Regiao")),
            )
            db.add(team)
            db.flush()
            name_to_id[team.name] = team.id
    return name_to_id


def _resolve_team_id(name_to_id: dict[str, int], name: str | None) -> int | None:
    if not name:
        return None
    return name_to_id.get(name.strip())


def _seed_games(db: Session, games_csv: Path, name_to_id: dict[str, int]) -> None:
    # games.csv and teams.csv come straight from the prototype (app/data/) and some
    # historical team names don't match exactly between the two (renames/aliases that
    # src/preprocessing/*.py partially handles but was never applied to these committed
    # CSVs). Rather than guess at fuzzy name matches and risk attributing a game to the
    # wrong team, unresolvable games are skipped; see test_seed.py for the current known
    # skip count. Reconciling the two CSVs is tracked as a follow-up, not fixed here.
    with games_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            home_id = _resolve_team_id(name_to_id, row["Mandante"])
            away_id = _resolve_team_id(name_to_id, row["Visitante"])
            if home_id is None or away_id is None:
                logger.warning(
                    "Skipping game on %s: unknown team(s) %r vs %r",
                    row["Data"],
                    row["Mandante"],
                    row["Visitante"],
                )
                continue

            home_score = row.get("Pontos Mandante")
            away_score = row.get("Pontos Visitante")
            game = Game(
                date=datetime.datetime.strptime(row["Data"], GAME_DATE_FORMAT),
                home_team_id=home_id,
                away_team_id=away_id,
                venue=_clean(row.get("Campo")),
                tournament=_clean(row.get("Torneio")),
                phase=_clean(row.get("Fase")),
                home_score=int(home_score) if home_score else None,
                away_score=int(away_score) if away_score else None,
                winner_team_id=_resolve_team_id(name_to_id, row.get("Vencedor")),
                defender_team_id=_resolve_team_id(
                    name_to_id, row.get("Defensor do Título")
                ),
            )
            db.add(game)


def seed_if_empty(db: Session, seed_data_dir: Path | None = None) -> None:
    """Idempotently seed teams/games from CSVs when the database is empty."""
    if db.query(Team).first() is not None:
        return

    data_dir = seed_data_dir if seed_data_dir is not None else settings.seed_data_dir
    name_to_id = _seed_teams(db, data_dir / "teams.csv")
    _seed_games(db, data_dir / "games.csv", name_to_id)
    db.commit()
