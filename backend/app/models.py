import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    logo_url: Mapped[str | None]
    home_city: Mapped[str | None]
    primary_color: Mapped[str | None]
    external_url: Mapped[str | None]
    state: Mapped[str | None]
    region: Mapped[str | None]


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime]
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    venue: Mapped[str | None]
    tournament: Mapped[str | None]
    phase: Mapped[str | None]
    home_score: Mapped[int | None]
    away_score: Mapped[int | None]
    winner_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    defender_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))

    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])
    winner_team: Mapped[Team | None] = relationship(foreign_keys=[winner_team_id])
    defender_team: Mapped[Team | None] = relationship(foreign_keys=[defender_team_id])
