import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_teams(client: TestClient) -> None:
    response = client.get("/api/teams")
    assert response.status_code == 200
    teams = response.json()
    assert len(teams) > 0
    assert {"id", "name", "logo_url"} <= teams[0].keys()


def test_get_team_not_found(client: TestClient) -> None:
    response = client.get("/api/teams/999999")
    assert response.status_code == 404


def test_list_games(client: TestClient) -> None:
    response = client.get("/api/games")
    assert response.status_code == 200
    games = response.json()
    assert len(games) > 0
    assert "home_team" in games[0]
    assert "away_team" in games[0]


def test_current_champion(client: TestClient) -> None:
    response = client.get("/api/cinturao/current")
    assert response.status_code == 200
    body = response.json()
    assert "team" in body
    assert "champion_since" in body


STATS_ENDPOINTS = [
    "/api/stats/title-defenses",
    "/api/stats/title-wins",
    "/api/stats/most-games",
    "/api/stats/most-losses",
    "/api/stats/title-losses",
    "/api/stats/days-with-title",
    "/api/stats/longest-reign",
    "/api/stats/longest-win-streak",
]


@pytest.mark.parametrize("path", STATS_ENDPOINTS)
def test_stats_endpoint_returns_leaderboard(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) > 0
    assert len(entries) <= 10
    assert {"team", "value"} <= entries[0].keys()
    assert "name" in entries[0]["team"]
    values = [entry["value"] for entry in entries]
    assert values == sorted(values, reverse=True)


def test_reign_timeline_returns_chronological_periods(client: TestClient) -> None:
    response = client.get("/api/stats/reign-timeline")
    assert response.status_code == 200
    timeline = response.json()
    assert len(timeline) > 0
    assert {"team", "start", "end", "ongoing"} <= timeline[0].keys()
    assert timeline[-1]["ongoing"] is True


def test_titles_by_region(client: TestClient) -> None:
    response = client.get("/api/stats/titles-by-region")
    assert response.status_code == 200
    regions = response.json()
    assert len(regions) > 0
    assert {"region", "value"} <= regions[0].keys()


def test_games_per_year_is_chronological(client: TestClient) -> None:
    response = client.get("/api/stats/games-per-year")
    assert response.status_code == 200
    years = [entry["year"] for entry in response.json()]
    assert years == sorted(years)


def test_score_margin_distribution_has_all_buckets(client: TestClient) -> None:
    response = client.get("/api/stats/score-margin-distribution")
    assert response.status_code == 200
    buckets = [entry["bucket"] for entry in response.json()]
    assert buckets == ["1-5", "6-10", "11-15", "16-20", "21+"]
