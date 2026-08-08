import datetime

from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services import llm_query


def test_build_prompt_embeds_grounding_data() -> None:
    messages = llm_query.build_prompt(
        "quem tem mais defesas",
        team_names=["Team A", "Team B"],
        regions=["sul", "sudeste"],
        states=["RS", "SP"],
    )

    assert messages[-1] == {"role": "user", "content": "quem tem mais defesas"}
    system = messages[0]["content"]
    assert "Team A, Team B" in system
    assert "sul, sudeste" in system
    assert "RS, SP" in system


def test_interpret_grounds_prompt_in_live_db_data(
    db_session: Session, monkeypatch
) -> None:
    team_a = Team(name="Team A", region="sul", state="RS")
    db_session.add(team_a)
    db_session.flush()
    db_session.add(
        Game(
            date=datetime.datetime(2020, 1, 1),
            home_team_id=team_a.id,
            away_team_id=team_a.id,
            winner_team_id=team_a.id,
            defender_team_id=None,
        )
    )
    db_session.commit()

    captured: dict[str, list[str]] = {}

    def fake_call_llm(messages: list[dict[str, str]]) -> llm_query.LLMQueryResponse:
        captured["system"] = [messages[0]["content"]]
        return llm_query.LLMQueryResponse(status="unsupported", reason="test")

    monkeypatch.setattr(llm_query, "_call_llm", fake_call_llm)

    result = llm_query.interpret(db_session, "alguma pergunta")

    assert result.status == "unsupported"
    assert "Team A" in captured["system"][0]
    assert "sul" in captured["system"][0]
    assert "RS" in captured["system"][0]


def test_call_llm_wraps_failures(monkeypatch) -> None:
    def boom(**kwargs: object) -> None:
        raise RuntimeError("network down")

    monkeypatch.setattr("app.services.llm_query.completion", boom)

    try:
        llm_query._call_llm([{"role": "user", "content": "x"}])
    except llm_query.AssistantLLMError as exc:
        assert "network down" in str(exc)
    else:
        raise AssertionError("expected AssistantLLMError")
