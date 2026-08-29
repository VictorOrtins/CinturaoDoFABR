import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
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
    __table_args__ = (
        # Natural key for sync upserts. Score is deliberately excluded: a
        # corrected score on an already-synced game should update the row, not
        # be treated as a new one (see docs/DATA_PIPELINE.md's Phase 1 note).
        UniqueConstraint(
            "date",
            "home_team_id",
            "away_team_id",
            "tournament",
            name="uq_game_identity",
        ),
    )

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
