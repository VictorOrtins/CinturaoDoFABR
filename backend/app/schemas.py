import datetime

from pydantic import BaseModel, ConfigDict


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    logo_url: str | None
    home_city: str | None
    primary_color: str | None
    external_url: str | None
    state: str | None
    region: str | None


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime.datetime
    home_team: TeamOut
    away_team: TeamOut
    venue: str | None
    tournament: str | None
    phase: str | None
    home_score: int | None
    away_score: int | None
    winner_team: TeamOut | None
    defender_team: TeamOut | None


class CurrentChampionOut(BaseModel):
    team: TeamOut
    champion_since: datetime.datetime
