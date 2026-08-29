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
    # "-" is the CSV's own sentinel for "no value" (e.g. Defensor do Título on
    # the very first game, before any title was won) - treat it as absent, the
    # same as an empty string, everywhere it appears.
    if value is None:
        return None
    value = value.strip()
    if value in ("", "-"):
        return None
    return value


def _sync_teams(db: Session, teams_csv: Path) -> dict[str, int]:
    name_to_team: dict[str, Team] = {t.name: t for t in db.query(Team).all()}
    with teams_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Nome"].strip()
            fields = {
                "logo_url": _clean(row.get("URL da Imagem")),
                "home_city": _clean(row.get("Sede")),
                "primary_color": _clean(row.get("Cor Primária")),
                "external_url": _clean(row.get("URL")),
                "state": _clean(row.get("Estado")),
                "region": _clean(row.get("Regiao")),
            }
            team = name_to_team.get(name)
            if team is None:
                team = Team(name=name, **fields)
                db.add(team)
                db.flush()
                name_to_team[name] = team
            else:
                for field, value in fields.items():
                    setattr(team, field, value)
    return {name: team.id for name, team in name_to_team.items()}


def _resolve_or_create_team_id(
    db: Session, name_to_id: dict[str, int], name: str | None
) -> int | None:
    # A game can reference a team name that never made it into teams.csv (a
    # scraper/site gap, see docs/DATA_PIPELINE.md's "unresolved teams" note).
    # A placeholder row keeps the game instead of silently dropping it -
    # Phase 1's check_unresolved_teams report is how these get noticed and
    # fixed for real.
    name = _clean(name)
    if not name:
        return None
    team_id = name_to_id.get(name)
    if team_id is not None:
        return team_id
    logger.warning("Creating placeholder team for unresolved name %r", name)
    team = Team(name=name)
    db.add(team)
    db.flush()
    name_to_id[name] = team.id
    return team.id


def _sync_games(db: Session, games_csv: Path, name_to_id: dict[str, int]) -> None:
    existing: dict[tuple, Game] = {
        (g.date, g.home_team_id, g.away_team_id, g.tournament): g
        for g in db.query(Game).all()
    }
    with games_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            home_id = _resolve_or_create_team_id(db, name_to_id, row["Mandante"])
            away_id = _resolve_or_create_team_id(db, name_to_id, row["Visitante"])
            if home_id is None or away_id is None:
                logger.warning(
                    "Skipping game on %s: missing team name(s) %r vs %r",
                    row["Data"],
                    row["Mandante"],
                    row["Visitante"],
                )
                continue

            date = datetime.datetime.strptime(row["Data"], GAME_DATE_FORMAT)
            tournament = _clean(row.get("Torneio"))
            key = (date, home_id, away_id, tournament)

            home_score = row.get("Pontos Mandante")
            away_score = row.get("Pontos Visitante")
            fields = {
                "venue": _clean(row.get("Campo")),
                "phase": _clean(row.get("Fase")),
                "home_score": int(home_score) if home_score else None,
                "away_score": int(away_score) if away_score else None,
                "winner_team_id": _resolve_or_create_team_id(
                    db, name_to_id, row.get("Vencedor")
                ),
                "defender_team_id": _resolve_or_create_team_id(
                    db, name_to_id, row.get("Defensor do Título")
                ),
            }

            game = existing.get(key)
            if game is None:
                game = Game(
                    date=date,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    tournament=tournament,
                    **fields,
                )
                db.add(game)
                db.flush()
                existing[key] = game
            else:
                for field, value in fields.items():
                    setattr(game, field, value)


def sync_from_csv(db: Session, seed_data_dir: Path | None = None) -> None:
    """Upserts teams/games from CSVs, keyed on natural identity (name for teams,
    date+home+away+tournament for games - score deliberately excluded, so a
    corrected score updates the row instead of creating a duplicate). Safe to
    call on every app startup: unchanged rows are a no-op, new rows insert, and
    changed mutable fields (score/venue/phase) update in place."""
    data_dir = seed_data_dir if seed_data_dir is not None else settings.seed_data_dir
    name_to_id = _sync_teams(db, data_dir / "teams.csv")
    _sync_games(db, data_dir / "games.csv", name_to_id)
    db.commit()
