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
