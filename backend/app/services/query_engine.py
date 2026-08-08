import datetime
import difflib
import statistics
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services.stats import UNKNOWN_REGION, ordered_games

TOP_N = 10

ChartType = Literal["leaderboard", "bar", "line"]
BucketKey = int | str
ResolvedFilters = tuple[int | None, str | None, str | None]


class Dimension(StrEnum):
    TEAM = "team"
    REGION = "region"
    YEAR = "year"


class TeamRole(StrEnum):
    HOME = "home"
    AWAY = "away"
    PARTICIPANT = "participant"
    WINNER = "winner"
    DEFENDER = "defender"
    LOSER = "loser"


class OutcomeFilter(StrEnum):
    BELT_CHANGED_HANDS = "belt_changed_hands"
    BELT_RETAINED = "belt_retained"


class MetricField(StrEnum):
    GAMES = "games"
    SCORE_MARGIN = "score_margin"
    POINTS_SCORED = "points_scored"
    POINTS_ALLOWED = "points_allowed"


class AggregationFunction(StrEnum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"


_SUBJECT_REQUIRED_METRICS = {MetricField.POINTS_SCORED, MetricField.POINTS_ALLOWED}


class FilterSpec(BaseModel):
    team_name: str | None = None
    region: str | None = None
    state: str | None = None
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None


class QuerySpec(BaseModel):
    group_by: Dimension
    team_role: TeamRole | None = None
    outcome_filter: OutcomeFilter | None = None
    metric_field: MetricField = MetricField.GAMES
    aggregation: AggregationFunction = AggregationFunction.COUNT
    filters: FilterSpec = Field(default_factory=FilterSpec)
    limit: int = Field(default=TOP_N, ge=1, le=TOP_N)

    @model_validator(mode="after")
    def _check_consistency(self) -> "QuerySpec":
        grouped_by_team = self.group_by in (Dimension.TEAM, Dimension.REGION)
        if grouped_by_team and self.team_role is None:
            raise ValueError("team_role is required when grouping by team or region")
        if self.metric_field in _SUBJECT_REQUIRED_METRICS and self.team_role is None:
            raise ValueError(f"metric_field={self.metric_field} requires a team_role")
        if (
            self.aggregation == AggregationFunction.COUNT
            and self.metric_field != MetricField.GAMES
        ):
            raise ValueError("count aggregation only applies to metric_field=games")
        if (
            self.aggregation != AggregationFunction.COUNT
            and self.metric_field == MetricField.GAMES
        ):
            raise ValueError("sum/avg aggregation requires a numeric metric_field")
        return self


@dataclass
class Bucket:
    label: str
    value: float
    team: Team | None = None


@dataclass
class QueryResult:
    chart_type: ChartType
    value_label: str
    buckets: list[Bucket]


class QueryEngineError(Exception):
    """Raised when a well-formed QuerySpec can't be resolved against real data."""


# --- role / outcome / metric registries -------------------------------------


def _loser_id(game: Game) -> int | None:
    if game.winner_team_id is None:
        return None
    if game.winner_team_id == game.home_team_id:
        return game.away_team_id
    return game.home_team_id


def _resolve_home(game: Game) -> list[int]:
    return [game.home_team_id]


def _resolve_away(game: Game) -> list[int]:
    return [game.away_team_id]


def _resolve_participant(game: Game) -> list[int]:
    return [game.home_team_id, game.away_team_id]


def _resolve_winner(game: Game) -> list[int]:
    return [game.winner_team_id] if game.winner_team_id is not None else []


def _resolve_defender(game: Game) -> list[int]:
    return [game.defender_team_id] if game.defender_team_id is not None else []


def _resolve_loser(game: Game) -> list[int]:
    loser_id = _loser_id(game)
    return [loser_id] if loser_id is not None else []


ROLE_RESOLVERS: dict[TeamRole, Callable[[Game], list[int]]] = {
    TeamRole.HOME: _resolve_home,
    TeamRole.AWAY: _resolve_away,
    TeamRole.PARTICIPANT: _resolve_participant,
    TeamRole.WINNER: _resolve_winner,
    TeamRole.DEFENDER: _resolve_defender,
    TeamRole.LOSER: _resolve_loser,
}


def _belt_changed_hands(game: Game) -> bool:
    # A defender of None means the belt had no prior holder (e.g. the very first title
    # game) — the winner still "captured" it, matching stats.py's get_title_wins.
    return game.winner_team_id != game.defender_team_id


def _belt_retained(game: Game) -> bool:
    if game.defender_team_id is None:
        return False
    return game.winner_team_id == game.defender_team_id


OUTCOME_PREDICATES: dict[OutcomeFilter, Callable[[Game], bool]] = {
    OutcomeFilter.BELT_CHANGED_HANDS: _belt_changed_hands,
    OutcomeFilter.BELT_RETAINED: _belt_retained,
}


def _metric_games(game: Game, subject_id: int | None) -> float | None:
    return 1.0


def _metric_score_margin(game: Game, subject_id: int | None) -> float | None:
    if game.home_score is None or game.away_score is None:
        return None
    return float(abs(game.home_score - game.away_score))


def _metric_points_scored(game: Game, subject_id: int | None) -> float | None:
    if subject_id == game.home_team_id:
        return float(game.home_score) if game.home_score is not None else None
    if subject_id == game.away_team_id:
        return float(game.away_score) if game.away_score is not None else None
    return None


def _metric_points_allowed(game: Game, subject_id: int | None) -> float | None:
    if subject_id == game.home_team_id:
        return float(game.away_score) if game.away_score is not None else None
    if subject_id == game.away_team_id:
        return float(game.home_score) if game.home_score is not None else None
    return None


METRIC_ACCESSORS: dict[MetricField, Callable[[Game, int | None], float | None]] = {
    MetricField.GAMES: _metric_games,
    MetricField.SCORE_MARGIN: _metric_score_margin,
    MetricField.POINTS_SCORED: _metric_points_scored,
    MetricField.POINTS_ALLOWED: _metric_points_allowed,
}

AGGREGATORS: dict[AggregationFunction, Callable[[list[float]], float]] = {
    AggregationFunction.COUNT: lambda values: float(len(values)),
    AggregationFunction.SUM: lambda values: float(sum(values)),
    AggregationFunction.AVG: statistics.mean,
    AggregationFunction.MAX: max,
    AggregationFunction.MIN: min,
}

_METRIC_LABELS: dict[MetricField, str] = {
    MetricField.GAMES: "Jogos",
    MetricField.SCORE_MARGIN: "Diferença de pontos",
    MetricField.POINTS_SCORED: "Pontos marcados",
    MetricField.POINTS_ALLOWED: "Pontos sofridos",
}

_ROLE_LABELS: dict[TeamRole, str] = {
    TeamRole.HOME: " como mandante",
    TeamRole.AWAY: " como visitante",
    TeamRole.PARTICIPANT: "",
    TeamRole.WINNER: " como vencedor",
    TeamRole.DEFENDER: " como defensor",
    TeamRole.LOSER: " como perdedor",
}

_AGGREGATION_LABELS: dict[AggregationFunction, str] = {
    AggregationFunction.COUNT: "",
    AggregationFunction.SUM: " (soma)",
    AggregationFunction.AVG: " (média)",
    AggregationFunction.MAX: " (máximo)",
    AggregationFunction.MIN: " (mínimo)",
}

_CHART_TYPE_BY_DIMENSION: dict[Dimension, ChartType] = {
    Dimension.TEAM: "leaderboard",
    Dimension.REGION: "bar",
    Dimension.YEAR: "line",
}


def _value_label(spec: QuerySpec) -> str:
    label = _METRIC_LABELS[spec.metric_field]
    if spec.team_role is not None:
        label += _ROLE_LABELS[spec.team_role]
    label += _AGGREGATION_LABELS[spec.aggregation]
    return label


# --- grounding data (for prompting + filter validation) ---------------------


def known_team_names(db: Session) -> list[str]:
    return sorted(name for (name,) in db.query(Team.name).all())


def known_regions(db: Session) -> list[str]:
    return sorted({region for (region,) in db.query(Team.region).all() if region})


def known_states(db: Session) -> list[str]:
    return sorted({state for (state,) in db.query(Team.state).all() if state})


def _best_match(value: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate.lower() == value.lower():
            return candidate
    matches = difflib.get_close_matches(value, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None


def _resolve_team_id(db: Session, name: str) -> int:
    teams = db.query(Team).all()
    match = _best_match(name, [team.name for team in teams])
    if match is None:
        raise QueryEngineError(f'Não encontrei o time "{name}".')
    return next(team.id for team in teams if team.name == match)


def _resolve_filters(db: Session, filters: FilterSpec) -> ResolvedFilters:
    team_id = _resolve_team_id(db, filters.team_name) if filters.team_name else None

    region = None
    if filters.region:
        region = _best_match(filters.region, known_regions(db))
        if region is None:
            raise QueryEngineError(f'Não encontrei a região "{filters.region}".')

    state = None
    if filters.state:
        state = _best_match(filters.state, known_states(db))
        if state is None:
            raise QueryEngineError(f'Não encontrei o estado "{filters.state}".')

    return team_id, region, state


# --- execution ----------------------------------------------------------


def _passes_team_filters(
    subject_id: int | None,
    game: Game,
    teams_by_id: dict[int, Team],
    team_id: int | None,
    region: str | None,
    state: str | None,
) -> bool:
    if subject_id is not None:
        if team_id is not None and subject_id != team_id:
            return False
        team = teams_by_id.get(subject_id)
        if region is not None and (team is None or team.region != region):
            return False
        if state is not None and (team is None or team.state != state):
            return False
        return True

    # No specific subject (team_role wasn't set): filters apply to the game as a whole.
    candidate_ids = (game.home_team_id, game.away_team_id)
    candidate_teams = [teams_by_id[tid] for tid in candidate_ids if tid in teams_by_id]
    if team_id is not None and team_id not in candidate_ids:
        return False
    if region is not None and not any(
        team.region == region for team in candidate_teams
    ):
        return False
    if state is not None and not any(team.state == state for team in candidate_teams):
        return False
    return True


TeamsById = dict[int, Team]


def _bucket_key(
    dimension: Dimension, game: Game, subject_id: int | None, teams_by_id: TeamsById
) -> tuple[BucketKey, Team | None]:
    if dimension == Dimension.TEAM:
        assert subject_id is not None
        return subject_id, teams_by_id[subject_id]
    if dimension == Dimension.REGION:
        assert subject_id is not None
        team = teams_by_id[subject_id]
        return team.region or UNKNOWN_REGION, None
    return game.date.year, None


def _bucket_label(key: BucketKey, team: Team | None) -> str:
    return team.name if team is not None else str(key)


def _filter_by_date_range(games: list[Game], filters: FilterSpec) -> list[Game]:
    if filters.date_from is not None:
        games = [g for g in games if g.date.date() >= filters.date_from]
    if filters.date_to is not None:
        games = [g for g in games if g.date.date() <= filters.date_to]
    return games


def execute(db: Session, spec: QuerySpec) -> QueryResult:
    team_id, region, state = _resolve_filters(db, spec.filters)
    teams_by_id = {team.id: team for team in db.query(Team).all()}

    games = _filter_by_date_range(ordered_games(db), spec.filters)

    role_resolver = None
    if spec.team_role is not None:
        role_resolver = ROLE_RESOLVERS[spec.team_role]
    outcome_predicate = None
    if spec.outcome_filter is not None:
        outcome_predicate = OUTCOME_PREDICATES[spec.outcome_filter]
    metric_accessor = METRIC_ACCESSORS[spec.metric_field]

    values_by_bucket: dict[BucketKey, list[float]] = defaultdict(list)
    team_by_bucket: dict[BucketKey, Team] = {}
    # A PARTICIPANT (or other multi-subject) role can resolve to two subjects for the
    # same game; when the bucket key doesn't depend on which subject it was (REGION
    # with two same-region teams, or YEAR, which never depends on the subject at all),
    # both would otherwise land in the same bucket and double-count one game.
    contributed: set[tuple[int, BucketKey]] = set()

    for game in games:
        if outcome_predicate is not None and not outcome_predicate(game):
            continue

        subjects = role_resolver(game) if role_resolver is not None else [None]
        for subject_id in subjects:
            passes = _passes_team_filters(
                subject_id, game, teams_by_id, team_id, region, state
            )
            if not passes:
                continue
            value = metric_accessor(game, subject_id)
            if value is None:
                continue
            key, team = _bucket_key(spec.group_by, game, subject_id, teams_by_id)
            if (game.id, key) in contributed:
                continue
            contributed.add((game.id, key))
            values_by_bucket[key].append(value)
            if team is not None:
                team_by_bucket[key] = team

    aggregator = AGGREGATORS[spec.aggregation]
    aggregated = [
        (key, aggregator(values), team_by_bucket.get(key))
        for key, values in values_by_bucket.items()
    ]

    if spec.group_by == Dimension.YEAR:
        aggregated.sort(key=lambda item: item[0])
    else:
        aggregated.sort(key=lambda item: item[1], reverse=True)
        aggregated = aggregated[: spec.limit]

    buckets = [
        Bucket(label=_bucket_label(key, team), value=value, team=team)
        for key, value, team in aggregated
    ]

    return QueryResult(
        chart_type=_CHART_TYPE_BY_DIMENSION[spec.group_by],
        value_label=_value_label(spec),
        buckets=buckets,
    )


# --- table queries (list raw games/teams instead of charting an aggregate) --

TABLE_LIMIT_DEFAULT = 25
TABLE_LIMIT_MAX = 100


class TableEntity(StrEnum):
    GAMES = "games"
    TEAMS = "teams"


class TableSpec(BaseModel):
    entity: TableEntity
    filters: FilterSpec = Field(default_factory=FilterSpec)
    limit: int = Field(default=TABLE_LIMIT_DEFAULT, ge=1, le=TABLE_LIMIT_MAX)


@dataclass
class TableResult:
    columns: list[str]
    rows: list[dict[str, str]]


_GAMES_TABLE_COLUMNS = ["Data", "Mandante", "Visitante", "Placar", "Campeão"]
_TEAMS_TABLE_COLUMNS = ["Time", "Cidade", "Estado", "Região"]


def _format_score(game: Game) -> str:
    if game.home_score is None or game.away_score is None:
        return "-"
    return f"{game.home_score} x {game.away_score}"


def _game_row(game: Game) -> dict[str, str]:
    winner = game.winner_team.name if game.winner_team is not None else "-"
    return {
        "Data": game.date.date().isoformat(),
        "Mandante": game.home_team.name,
        "Visitante": game.away_team.name,
        "Placar": _format_score(game),
        "Campeão": winner,
    }


def _team_row(team: Team) -> dict[str, str]:
    return {
        "Time": team.name,
        "Cidade": team.home_city or "-",
        "Estado": team.state or "-",
        "Região": team.region or UNKNOWN_REGION,
    }


def _table_games(
    db: Session,
    team_id: int | None,
    region: str | None,
    state: str | None,
    filters: FilterSpec,
    limit: int,
) -> TableResult:
    teams_by_id = {team.id: team for team in db.query(Team).all()}
    games = _filter_by_date_range(ordered_games(db), filters)
    rows = [
        _game_row(game)
        for game in games
        if _passes_team_filters(None, game, teams_by_id, team_id, region, state)
    ][:limit]
    return TableResult(columns=_GAMES_TABLE_COLUMNS, rows=rows)


def _table_teams(
    db: Session, team_id: int | None, region: str | None, state: str | None, limit: int
) -> TableResult:
    query = db.query(Team)
    if team_id is not None:
        query = query.filter(Team.id == team_id)
    if region is not None:
        query = query.filter(Team.region == region)
    if state is not None:
        query = query.filter(Team.state == state)
    teams = query.order_by(Team.name).limit(limit).all()
    rows = [_team_row(team) for team in teams]
    return TableResult(columns=_TEAMS_TABLE_COLUMNS, rows=rows)


def execute_table(db: Session, spec: TableSpec) -> TableResult:
    team_id, region, state = _resolve_filters(db, spec.filters)
    if spec.entity == TableEntity.TEAMS:
        return _table_teams(db, team_id, region, state, spec.limit)
    return _table_games(db, team_id, region, state, spec.filters, spec.limit)
