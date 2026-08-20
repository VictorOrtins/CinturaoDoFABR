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
from app.services import teams as teams_service
from app.services.stats import UNKNOWN_REGION, ordered_games

TOP_N = 10

ChartType = Literal["leaderboard", "bar", "line"]
BucketKey = int | str | float | datetime.date
TeamsById = dict[int, Team]


class FieldEntity(StrEnum):
    TEAM = "team"
    GAME = "game"


class Transform(StrEnum):
    IDENTITY = "identity"
    YEAR = "year"
    DECADE = "decade"
    MONTH = "month"
    INITIAL = "initial"


class ColumnKind(StrEnum):
    STRING = "string"
    DATE = "date"
    NUMBER = "number"


# Whitelisted, queryable columns per entity. Deliberately excludes columns with
# no meaningful query vocabulary (team.primary_color/logo_url/external_url — no
# color-name vocabulary exists, same reasoning the assistant already uses to
# decline "times vermelhos"; game.id/home_team_id/etc — team identity is reached
# via team_role, not a raw id column).
_COLUMN_KINDS: dict[FieldEntity, dict[str, ColumnKind]] = {
    FieldEntity.TEAM: {
        "name": ColumnKind.STRING,
        "region": ColumnKind.STRING,
        "state": ColumnKind.STRING,
        "home_city": ColumnKind.STRING,
    },
    FieldEntity.GAME: {
        "date": ColumnKind.DATE,
        "venue": ColumnKind.STRING,
        "tournament": ColumnKind.STRING,
        "phase": ColumnKind.STRING,
        "home_score": ColumnKind.NUMBER,
        "away_score": ColumnKind.NUMBER,
    },
}

_TRANSFORMS_BY_KIND: dict[ColumnKind, set[Transform]] = {
    ColumnKind.STRING: {Transform.IDENTITY, Transform.INITIAL},
    ColumnKind.DATE: {
        Transform.IDENTITY,
        Transform.YEAR,
        Transform.DECADE,
        Transform.MONTH,
    },
    ColumnKind.NUMBER: {Transform.IDENTITY},
}


class FieldRef(BaseModel):
    entity: FieldEntity
    column: str
    transform: Transform = Transform.IDENTITY

    @model_validator(mode="after")
    def _check_field(self) -> "FieldRef":
        columns = _COLUMN_KINDS[self.entity]
        if self.column not in columns:
            raise ValueError(f'campo desconhecido: "{self.entity}.{self.column}"')
        allowed_transforms = _TRANSFORMS_BY_KIND[columns[self.column]]
        if self.transform not in allowed_transforms:
            raise ValueError(
                f'transform "{self.transform}" inválido para '
                f'"{self.entity}.{self.column}"'
            )
        return self

    @property
    def kind(self) -> ColumnKind:
        return _COLUMN_KINDS[self.entity][self.column]


def _is_team_identity(field: FieldRef) -> bool:
    return (
        field.entity == FieldEntity.TEAM
        and field.column == "name"
        and field.transform == Transform.IDENTITY
    )


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
    TEAMS = "teams"
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
_COUNT_ONLY_METRICS = {MetricField.GAMES, MetricField.TEAMS}


class FilterOp(StrEnum):
    EQUALS = "equals"
    GTE = "gte"
    LTE = "lte"


class FilterClause(BaseModel):
    field: FieldRef
    op: FilterOp
    value: str

    @model_validator(mode="after")
    def _check_op(self) -> "FilterClause":
        is_range_op = self.op in (FilterOp.GTE, FilterOp.LTE)
        if is_range_op and self.field.kind == ColumnKind.STRING:
            raise ValueError("gte/lte não se aplica a campos de texto")
        return self


class QuerySpec(BaseModel):
    group_by: FieldRef
    team_role: TeamRole | None = None
    outcome_filter: OutcomeFilter | None = None
    metric_field: MetricField = MetricField.GAMES
    aggregation: AggregationFunction = AggregationFunction.COUNT
    filters: list[FilterClause] = Field(default_factory=list)
    sort_by: Literal["value", "key"] | None = None
    direction: Literal["asc", "desc"] | None = None
    limit: int = Field(default=TOP_N, ge=1, le=TOP_N)

    @model_validator(mode="after")
    def _check_consistency(self) -> "QuerySpec":
        if self.metric_field == MetricField.TEAMS:
            if self.group_by.entity != FieldEntity.TEAM:
                raise ValueError("metric_field=teams requires group_by on a team field")
            if self.team_role is not None:
                raise ValueError("team_role does not apply to metric_field=teams")
            if self.outcome_filter is not None:
                raise ValueError("outcome_filter does not apply to metric_field=teams")
            if any(clause.field.entity == FieldEntity.GAME for clause in self.filters):
                raise ValueError(
                    "game-field filters do not apply to metric_field=teams"
                )
            if self.aggregation != AggregationFunction.COUNT:
                raise ValueError("metric_field=teams only supports aggregation=count")
            return self

        if self.group_by.entity == FieldEntity.TEAM and self.team_role is None:
            raise ValueError(
                "team_role is required when group_by references a team field"
            )
        if self.metric_field in _SUBJECT_REQUIRED_METRICS and self.team_role is None:
            raise ValueError(f"metric_field={self.metric_field} requires a team_role")
        if (
            self.aggregation == AggregationFunction.COUNT
            and self.metric_field not in _COUNT_ONLY_METRICS
        ):
            raise ValueError("count aggregation only applies to metric_field=games")
        if (
            self.aggregation != AggregationFunction.COUNT
            and self.metric_field in _COUNT_ONLY_METRICS
        ):
            raise ValueError(
                "sum/avg/max/min aggregation requires a numeric metric_field"
            )
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
    """Raised when a well-formed spec can't be resolved against real data."""


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
    MetricField.TEAMS: "Times",
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


def _value_label(spec: QuerySpec) -> str:
    label = _METRIC_LABELS[spec.metric_field]
    if spec.team_role is not None:
        label += _ROLE_LABELS[spec.team_role]
    label += _AGGREGATION_LABELS[spec.aggregation]
    return label


def _chart_type(group_by: FieldRef) -> ChartType:
    if _is_team_identity(group_by):
        return "leaderboard"
    if group_by.kind == ColumnKind.DATE and group_by.transform in (
        Transform.YEAR,
        Transform.DECADE,
    ):
        return "line"
    return "bar"


# --- field extraction / transforms -------------------------------------


def _apply_transform(transform: Transform, raw: object) -> BucketKey:
    if transform == Transform.IDENTITY:
        return raw.date() if isinstance(raw, datetime.datetime) else raw  # type: ignore[return-value]
    if transform == Transform.INITIAL:
        text = str(raw)
        return text[0].upper() if text else UNKNOWN_REGION
    assert isinstance(raw, datetime.datetime)
    if transform == Transform.YEAR:
        return raw.year
    if transform == Transform.DECADE:
        return (raw.year // 10) * 10
    return raw.month  # MONTH


def _extract(
    field: FieldRef, subject_team: Team | None, game: Game | None
) -> BucketKey | None:
    if field.entity == FieldEntity.TEAM:
        if subject_team is None:
            return None
        raw = getattr(subject_team, field.column)
    else:
        assert game is not None
        raw = getattr(game, field.column)
    if raw is None:
        return None
    return _apply_transform(field.transform, raw)


def _bucket_key(
    group_by: FieldRef, subject_team: Team | None, game: Game
) -> tuple[BucketKey, Team | None]:
    value = _extract(group_by, subject_team, game)
    if value is None:
        value = UNKNOWN_REGION
    team = subject_team if _is_team_identity(group_by) else None
    return value, team


def _bucket_label(key: BucketKey, team: Team | None) -> str:
    return team.name if team is not None else str(key)


# --- grounding data (for prompting + filter validation) ---------------------


def known_field_values(db: Session, field: FieldRef) -> list[str]:
    model = Team if field.entity == FieldEntity.TEAM else Game
    column = getattr(model, field.column)
    rows = db.query(column).distinct().all()
    return sorted({str(value) for (value,) in rows if value is not None})


def known_team_names(db: Session) -> list[str]:
    return known_field_values(db, FieldRef(entity=FieldEntity.TEAM, column="name"))


def known_regions(db: Session) -> list[str]:
    return known_field_values(db, FieldRef(entity=FieldEntity.TEAM, column="region"))


def known_states(db: Session) -> list[str]:
    return known_field_values(db, FieldRef(entity=FieldEntity.TEAM, column="state"))


def known_venues(db: Session) -> list[str]:
    return known_field_values(db, FieldRef(entity=FieldEntity.GAME, column="venue"))


def known_tournaments(db: Session) -> list[str]:
    field = FieldRef(entity=FieldEntity.GAME, column="tournament")
    return known_field_values(db, field)


def known_phases(db: Session) -> list[str]:
    return known_field_values(db, FieldRef(entity=FieldEntity.GAME, column="phase"))


def _best_match(value: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate.lower() == value.lower():
            return candidate
    matches = difflib.get_close_matches(value, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None


@dataclass
class ResolvedClause:
    field: FieldRef
    op: FilterOp
    value: object


def _resolve_clause(db: Session, clause: FilterClause) -> ResolvedClause:
    kind = clause.field.kind

    if (
        clause.op == FilterOp.EQUALS
        and clause.field.transform == Transform.IDENTITY
        and kind == ColumnKind.STRING
    ):
        candidates = known_field_values(db, clause.field)
        match = _best_match(clause.value, candidates)
        if match is None:
            raise QueryEngineError(
                f'Não encontrei "{clause.value}" para '
                f"{clause.field.entity}.{clause.field.column}."
            )
        return ResolvedClause(clause.field, clause.op, match)

    if kind == ColumnKind.DATE and clause.field.transform == Transform.IDENTITY:
        try:
            parsed_date = datetime.date.fromisoformat(clause.value)
        except ValueError as exc:
            raise QueryEngineError(f'Data inválida: "{clause.value}".') from exc
        return ResolvedClause(clause.field, clause.op, parsed_date)

    if kind == ColumnKind.DATE:
        try:
            return ResolvedClause(clause.field, clause.op, int(clause.value))
        except ValueError as exc:
            raise QueryEngineError(
                f'Valor inválido: "{clause.value}".'
            ) from exc

    if kind == ColumnKind.NUMBER:
        try:
            return ResolvedClause(clause.field, clause.op, float(clause.value))
        except ValueError as exc:
            raise QueryEngineError(
                f'Valor inválido: "{clause.value}".'
            ) from exc

    # STRING column with a non-identity transform (initial) — direct, no fuzzy match.
    return ResolvedClause(clause.field, clause.op, clause.value)


def _compare(extracted: BucketKey | None, op: FilterOp, value: object) -> bool:
    if extracted is None:
        return False
    if op == FilterOp.EQUALS:
        if isinstance(extracted, str) and isinstance(value, str):
            return extracted.lower() == value.lower()
        return extracted == value
    if op == FilterOp.GTE:
        return extracted >= value  # type: ignore[operator]
    return extracted <= value  # type: ignore[operator]  # LTE


# --- execution: game-based metrics (games/score_margin/points_*) ------------


def _clause_passes(
    clause: ResolvedClause,
    game: Game,
    teams_by_id: TeamsById,
    subject_team: Team | None,
) -> bool:
    if clause.field.entity == FieldEntity.GAME:
        return _compare(_extract(clause.field, None, game), clause.op, clause.value)
    if subject_team is not None:
        extracted = _extract(clause.field, subject_team, game)
        return _compare(extracted, clause.op, clause.value)
    candidates = (teams_by_id[game.home_team_id], teams_by_id[game.away_team_id])
    return any(
        _compare(_extract(clause.field, team, game), clause.op, clause.value)
        for team in candidates
    )


def _clause_passes_team(clause: ResolvedClause, team: Team) -> bool:
    return _compare(_extract(clause.field, team, None), clause.op, clause.value)


AggregatedBucket = tuple[BucketKey, float, Team | None]


def _sort_and_limit(
    aggregated: list[AggregatedBucket],
    chart_type: ChartType,
    sort_by: Literal["value", "key"] | None,
    direction: Literal["asc", "desc"] | None,
    limit: int,
) -> list[AggregatedBucket]:
    effective_sort_by = sort_by or ("key" if chart_type == "line" else "value")
    effective_direction = direction or ("asc" if chart_type == "line" else "desc")
    reverse = effective_direction == "desc"

    if effective_sort_by == "key":
        return sorted(aggregated, key=lambda item: item[0], reverse=reverse)  # type: ignore[arg-type,return-value]

    sorted_aggregated = sorted(aggregated, key=lambda item: item[1], reverse=reverse)
    return sorted_aggregated[:limit]


def _finalize(spec: QuerySpec, aggregated: list[AggregatedBucket]) -> QueryResult:
    chart_type = _chart_type(spec.group_by)
    aggregated = _sort_and_limit(
        aggregated, chart_type, spec.sort_by, spec.direction, spec.limit
    )
    buckets = [
        Bucket(label=_bucket_label(key, team), value=value, team=team)
        for key, value, team in aggregated
    ]
    return QueryResult(
        chart_type=chart_type, value_label=_value_label(spec), buckets=buckets
    )


def _execute_game_metric(db: Session, spec: QuerySpec) -> QueryResult:
    resolved_clauses = [_resolve_clause(db, clause) for clause in spec.filters]
    teams_by_id = {team.id: team for team in db.query(Team).all()}
    games = ordered_games(db)

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
            subject_team = teams_by_id[subject_id] if subject_id is not None else None
            if not all(
                _clause_passes(clause, game, teams_by_id, subject_team)
                for clause in resolved_clauses
            ):
                continue
            value = metric_accessor(game, subject_id)
            if value is None:
                continue
            key, team = _bucket_key(spec.group_by, subject_team, game)
            if (game.id, key) in contributed:
                continue
            contributed.add((game.id, key))
            values_by_bucket[key].append(value)
            if team is not None:
                team_by_bucket[key] = team

    aggregator = AGGREGATORS[spec.aggregation]
    aggregated: list[AggregatedBucket] = [
        (key, aggregator(values), team_by_bucket.get(key))
        for key, values in values_by_bucket.items()
    ]
    return _finalize(spec, aggregated)


# --- execution: team-count metric (metric_field=teams) -----------------------


def _execute_team_count(db: Session, spec: QuerySpec) -> QueryResult:
    resolved_clauses = [_resolve_clause(db, clause) for clause in spec.filters]
    teams = teams_service.list_teams(db, played_only=True)

    counts: dict[BucketKey, int] = defaultdict(int)
    team_by_bucket: dict[BucketKey, Team] = {}
    for team in teams:
        if not all(_clause_passes_team(clause, team) for clause in resolved_clauses):
            continue
        value = _extract(spec.group_by, team, None)
        key = value if value is not None else UNKNOWN_REGION
        counts[key] += 1
        if _is_team_identity(spec.group_by):
            team_by_bucket[key] = team

    aggregated: list[AggregatedBucket] = [
        (key, float(count), team_by_bucket.get(key)) for key, count in counts.items()
    ]
    return _finalize(spec, aggregated)


def execute(db: Session, spec: QuerySpec) -> QueryResult:
    if spec.metric_field == MetricField.TEAMS:
        return _execute_team_count(db, spec)
    return _execute_game_metric(db, spec)


# --- table queries (list raw games/teams instead of charting an aggregate) --

TABLE_LIMIT_DEFAULT = 25
TABLE_LIMIT_MAX = 100


class TableEntity(StrEnum):
    GAMES = "games"
    TEAMS = "teams"


class TableSpec(BaseModel):
    entity: TableEntity
    filters: list[FilterClause] = Field(default_factory=list)
    sort_by: FieldRef | None = None
    direction: Literal["asc", "desc"] = "asc"
    limit: int = Field(default=TABLE_LIMIT_DEFAULT, ge=1, le=TABLE_LIMIT_MAX)

    @model_validator(mode="after")
    def _check_consistency(self) -> "TableSpec":
        is_games = self.entity == TableEntity.GAMES
        expected_entity = FieldEntity.GAME if is_games else FieldEntity.TEAM
        if self.sort_by is not None and self.sort_by.entity != expected_entity:
            raise ValueError(
                f"sort_by must reference entity={expected_entity} for {self.entity}"
            )
        if self.entity == TableEntity.TEAMS and any(
            clause.field.entity == FieldEntity.GAME for clause in self.filters
        ):
            raise ValueError("game-field filters do not apply to entity=teams")
        return self


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
    resolved_clauses: list[ResolvedClause],
    sort_by: FieldRef | None,
    direction: Literal["asc", "desc"],
    limit: int,
) -> TableResult:
    teams_by_id = {team.id: team for team in db.query(Team).all()}

    def _passes(game: Game) -> bool:
        return all(
            _clause_passes(clause, game, teams_by_id, None)
            for clause in resolved_clauses
        )

    games = [game for game in ordered_games(db) if _passes(game)]
    if sort_by is not None:
        games = sorted(
            games,
            key=lambda game: _extract(sort_by, None, game) or "",  # type: ignore[arg-type]
            reverse=(direction == "desc"),
        )
    rows = [_game_row(game) for game in games][:limit]
    return TableResult(columns=_GAMES_TABLE_COLUMNS, rows=rows)


def _table_teams(
    db: Session,
    resolved_clauses: list[ResolvedClause],
    sort_by: FieldRef | None,
    direction: Literal["asc", "desc"],
    limit: int,
) -> TableResult:
    teams = [
        team
        for team in db.query(Team).all()
        if all(_clause_passes_team(clause, team) for clause in resolved_clauses)
    ]
    if sort_by is not None:
        teams = sorted(
            teams,
            key=lambda team: _extract(sort_by, team, None) or "",  # type: ignore[arg-type]
            reverse=(direction == "desc"),
        )
    else:
        teams = sorted(teams, key=lambda team: team.name)
    rows = [_team_row(team) for team in teams[:limit]]
    return TableResult(columns=_TEAMS_TABLE_COLUMNS, rows=rows)


def execute_table(db: Session, spec: TableSpec) -> TableResult:
    resolved_clauses = [_resolve_clause(db, clause) for clause in spec.filters]
    sort_by, direction, limit = spec.sort_by, spec.direction, spec.limit
    if spec.entity == TableEntity.TEAMS:
        return _table_teams(db, resolved_clauses, sort_by, direction, limit)
    return _table_games(db, resolved_clauses, sort_by, direction, limit)
