import pytest
from fastapi.testclient import TestClient

from app.services import llm_query, query_engine


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


def test_list_teams_played_only_is_a_strict_subset(client: TestClient) -> None:
    all_teams = client.get("/api/teams").json()
    played_teams = client.get("/api/teams", params={"played": True}).json()

    assert 0 < len(played_teams) < len(all_teams)
    assert {t["id"] for t in played_teams} <= {t["id"] for t in all_teams}


def test_list_team_games(client: TestClient) -> None:
    team_id = client.get("/api/teams", params={"played": True}).json()[0]["id"]

    response = client.get(f"/api/teams/{team_id}/games")

    assert response.status_code == 200
    games = response.json()
    assert len(games) > 0
    for game in games:
        assert team_id in (game["home_team"]["id"], game["away_team"]["id"])


def test_list_team_games_not_found(client: TestClient) -> None:
    response = client.get("/api/teams/999999/games")
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


def test_assistant_query_returns_503_when_unconfigured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "openrouter_api_key", None)

    response = client.post(
        "/api/assistant/query", json={"question": "quem tem mais defesas"}
    )

    assert response.status_code == 503


def test_assistant_query_ok_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    spec = query_engine.QuerySpec(
        group_by=query_engine.Dimension.TEAM, team_role=query_engine.TeamRole.DEFENDER
    )
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(status="ok", spec=spec),
    )

    response = client.post(
        "/api/assistant/query", json={"question": "quem tem mais defesas"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["output"] == "chart"
    assert body["chart"]["chart_type"] == "leaderboard"
    assert "primary_color" in body["chart"]["leaderboard"][0]["team"]


def test_assistant_query_unsupported_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(
            status="unsupported", reason="Não temos dados de jogadores."
        ),
    )

    response = client.post(
        "/api/assistant/query", json={"question": "quem fez mais touchdowns"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unsupported"
    assert body["chart"] is None
    assert body["table"] is None


def test_assistant_query_rejects_empty_question(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")

    response = client.post("/api/assistant/query", json={"question": ""})

    assert response.status_code == 422


def test_assistant_query_table_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    table_spec = query_engine.TableSpec(entity=query_engine.TableEntity.GAMES, limit=5)
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(
            status="ok", output="table", table=table_spec
        ),
    )

    response = client.post(
        "/api/assistant/query", json={"question": "quais jogos aconteceram"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["output"] == "table"
    assert body["chart"] is None
    expected_columns = ["Data", "Mandante", "Visitante", "Placar", "Campeão"]
    assert body["table"]["columns"] == expected_columns
    assert len(body["table"]["rows"]) == 5
