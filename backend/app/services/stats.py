import datetime
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.models import Game, Team

TOP_N = 10


@dataclass
class LeaderboardEntry:
    team: Team
    value: int


@dataclass
class ReignPeriod:
    team_id: int
    start: datetime.datetime
    end: datetime.datetime
    ongoing: bool


@dataclass
class ReignTimelineEntry:
    team: Team
    start: datetime.datetime
    end: datetime.datetime
    ongoing: bool


@dataclass
class RegionCount:
    region: str
    value: int


@dataclass
class YearCount:
    year: int
    value: int


@dataclass
class MarginBucketCount:
    bucket: str
    value: int


UNKNOWN_REGION = "Não informado"
BUCKET_LABELS = ["1-5", "6-10", "11-15", "16-20", "21+"]


def ordered_games(db: Session) -> list[Game]:
    return (
        db.query(Game)
        .options(joinedload(Game.winner_team), joinedload(Game.defender_team))
        .order_by(Game.date.asc(), Game.id.asc())
        .all()
    )


def _winner_id(game: Game) -> int:
    assert game.winner_team_id is not None, "every title game must have a winner"
    return game.winner_team_id


def _leaderboard(counts: dict[int, int], db: Session) -> list[LeaderboardEntry]:
    teams_by_id = {team.id: team for team in db.query(Team).all()}
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:TOP_N]
    return [
        LeaderboardEntry(team=teams_by_id[team_id], value=value)
        for team_id, value in ranked
    ]


def get_title_defenses(db: Session) -> list[LeaderboardEntry]:
    """Times a team appeared as defender in a title game."""
    counts: dict[int, int] = defaultdict(int)
    for game in ordered_games(db):
        if game.defender_team_id is not None:
            counts[game.defender_team_id] += 1
    return _leaderboard(counts, db)


def get_title_wins(db: Session) -> list[LeaderboardEntry]:
    """Times a team captured the belt from a different holder (or won it outright)."""
    counts: dict[int, int] = defaultdict(int)
    for game in ordered_games(db):
        if _winner_id(game) != game.defender_team_id:
            counts[_winner_id(game)] += 1
    return _leaderboard(counts, db)


def get_most_games_played(db: Session) -> list[LeaderboardEntry]:
    """Total appearances (home or away) in title games."""
    counts: dict[int, int] = defaultdict(int)
    for game in ordered_games(db):
        counts[game.home_team_id] += 1
        counts[game.away_team_id] += 1
    return _leaderboard(counts, db)


def get_most_game_losses(db: Session) -> list[LeaderboardEntry]:
    """Raw match losses in title games, regardless of whether the belt changed hands."""
    counts: dict[int, int] = defaultdict(int)
    for game in ordered_games(db):
        winner_id = _winner_id(game)
        if winner_id != game.home_team_id:
            counts[game.home_team_id] += 1
        if winner_id != game.away_team_id:
            counts[game.away_team_id] += 1
    return _leaderboard(counts, db)


def get_title_losses(db: Session) -> list[LeaderboardEntry]:
    """Times a team lost the belt to a challenger."""
    counts: dict[int, int] = defaultdict(int)
    for game in ordered_games(db):
        defender_id = game.defender_team_id
        if defender_id is not None and _winner_id(game) != defender_id:
            counts[defender_id] += 1
    return _leaderboard(counts, db)


def _reign_periods(
    games: list[Game], now: datetime.datetime | None = None
) -> list[ReignPeriod]:
    """Every holding period in chronological order, including the ongoing one."""
    if not games:
        return []
    periods: list[ReignPeriod] = []
    champion_id = _winner_id(games[0])
    reign_start = games[0].date
    for game in games[1:]:
        winner_id = _winner_id(game)
        if winner_id != champion_id:
            periods.append(
                ReignPeriod(champion_id, reign_start, game.date, ongoing=False)
            )
            champion_id = winner_id
            reign_start = game.date
    reign_end = now or datetime.datetime.now()
    periods.append(ReignPeriod(champion_id, reign_start, reign_end, ongoing=True))
    return periods


def get_days_with_title(
    db: Session, now: datetime.datetime | None = None
) -> list[LeaderboardEntry]:
    """Cumulative days each team has held the belt, across all of its reigns."""
    totals: dict[int, int] = defaultdict(int)
    for period in _reign_periods(ordered_games(db), now):
        totals[period.team_id] += (period.end - period.start).days
    return _leaderboard(totals, db)


def get_longest_reign(
    db: Session, now: datetime.datetime | None = None
) -> list[LeaderboardEntry]:
    """Longest single unbroken reign, in days, per team."""
    longest: dict[int, int] = defaultdict(int)
    for period in _reign_periods(ordered_games(db), now):
        days = (period.end - period.start).days
        longest[period.team_id] = max(longest[period.team_id], days)
    return _leaderboard(longest, db)


def get_reign_timeline(
    db: Session, now: datetime.datetime | None = None
) -> list[ReignTimelineEntry]:
    """Every championship reign in chronological order, for a timeline view."""
    teams_by_id = {team.id: team for team in db.query(Team).all()}
    return [
        ReignTimelineEntry(
            team=teams_by_id[period.team_id],
            start=period.start,
            end=period.end,
            ongoing=period.ongoing,
        )
        for period in _reign_periods(ordered_games(db), now)
    ]


def get_longest_win_streak(db: Session) -> list[LeaderboardEntry]:
    """Longest streak of consecutive title games won by the same team."""
    games = ordered_games(db)
    longest: dict[int, int] = defaultdict(int)
    if games:
        current_id = _winner_id(games[0])
        current_streak = 1
        for game in games[1:]:
            winner_id = _winner_id(game)
            if winner_id == current_id:
                current_streak += 1
            else:
                longest[current_id] = max(longest[current_id], current_streak)
                current_id = winner_id
                current_streak = 1
        longest[current_id] = max(longest[current_id], current_streak)
    return _leaderboard(longest, db)


def get_titles_by_region(db: Session) -> list[RegionCount]:
    """Title captures grouped by the winning team's region."""
    teams_by_id = {team.id: team for team in db.query(Team).all()}
    counts: dict[str, int] = defaultdict(int)
    for game in ordered_games(db):
        if _winner_id(game) != game.defender_team_id:
            region = teams_by_id[_winner_id(game)].region or UNKNOWN_REGION
            counts[region] += 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [RegionCount(region=region, value=value) for region, value in ranked]


def get_games_per_year(db: Session) -> list[YearCount]:
    """Number of title games played per calendar year, chronologically."""
    counts: dict[int, int] = defaultdict(int)
    for game in ordered_games(db):
        counts[game.date.year] += 1
    return [YearCount(year=year, value=counts[year]) for year in sorted(counts)]


def _margin_bucket(margin: int) -> str:
    if margin <= 5:
        return "1-5"
    if margin <= 10:
        return "6-10"
    if margin <= 15:
        return "11-15"
    if margin <= 20:
        return "16-20"
    return "21+"


def get_score_margin_distribution(db: Session) -> list[MarginBucketCount]:
    """Title games bucketed by how close the final score was."""
    counts: dict[str, int] = defaultdict(int)
    for game in ordered_games(db):
        if game.home_score is None or game.away_score is None:
            continue
        counts[_margin_bucket(abs(game.home_score - game.away_score))] += 1
    return [
        MarginBucketCount(bucket=label, value=counts[label]) for label in BUCKET_LABELS
    ]
