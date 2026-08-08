import datetime

from sqlalchemy.orm import Session

from app.models import Game, Team
from app.services import assistant, llm_query, query_engine


def _seed_one_game(db: Session) -> Team:
    team_a = Team(name="Team A")
    team_b = Team(name="Team B")
    db.add_all([team_a, team_b])
    db.flush()
    db.add(
        Game(
            date=datetime.datetime(2020, 1, 1),
            home_team_id=team_a.id,
            away_team_id=team_b.id,
            winner_team_id=team_a.id,
            defender_team_id=None,
        )
    )
    db.commit()
    return team_a


def test_answer_question_ok_path(db_session: Session, monkeypatch) -> None:
    _seed_one_game(db_session)
    spec = query_engine.QuerySpec(
        group_by=query_engine.Dimension.TEAM, team_role=query_engine.TeamRole.WINNER
    )
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(status="ok", spec=spec),
    )

    answer = assistant.answer_question(db_session, "quem ganhou mais jogos")

    assert answer.status == "ok"
    assert answer.output == "chart"
    assert answer.message is None
    assert answer.chart is not None
    assert answer.chart.buckets[0].label == "Team A"


def test_answer_question_unsupported_path(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(
            status="unsupported", reason="Não temos dados de jogadores."
        ),
    )

    answer = assistant.answer_question(db_session, "quem fez mais touchdowns")

    assert answer.status == "unsupported"
    assert answer.message == "Não temos dados de jogadores."
    assert answer.chart is None
    assert answer.table is None


def test_answer_question_llm_failure_path(db_session: Session, monkeypatch) -> None:
    def boom(db: Session, question: str) -> llm_query.LLMQueryResponse:
        raise llm_query.AssistantLLMError("timeout")

    monkeypatch.setattr(llm_query, "interpret", boom)

    answer = assistant.answer_question(db_session, "qualquer pergunta")

    assert answer.status == "error"
    assert answer.chart is None


def test_answer_question_unresolvable_filter_path(
    db_session: Session, monkeypatch
) -> None:
    _seed_one_game(db_session)
    spec = query_engine.QuerySpec(
        group_by=query_engine.Dimension.TEAM,
        team_role=query_engine.TeamRole.WINNER,
        filters=query_engine.FilterSpec(team_name="Does Not Exist At All"),
    )
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(status="ok", spec=spec),
    )

    answer = assistant.answer_question(db_session, "jogos do time inexistente")

    assert answer.status == "error"
    assert answer.chart is None


def test_answer_question_empty_result_path(db_session: Session, monkeypatch) -> None:
    spec = query_engine.QuerySpec(
        group_by=query_engine.Dimension.TEAM, team_role=query_engine.TeamRole.WINNER
    )
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(status="ok", spec=spec),
    )

    answer = assistant.answer_question(db_session, "quem ganhou mais jogos")

    assert answer.status == "ok"
    assert answer.message is not None
    assert answer.chart is not None
    assert answer.chart.buckets == []


def test_answer_question_table_path(db_session: Session, monkeypatch) -> None:
    _seed_one_game(db_session)
    table_spec = query_engine.TableSpec(entity=query_engine.TableEntity.GAMES)
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(
            status="ok", output="table", table=table_spec
        ),
    )

    answer = assistant.answer_question(db_session, "quais jogos o Team A jogou")

    assert answer.status == "ok"
    assert answer.output == "table"
    assert answer.chart is None
    assert answer.table is not None
    assert len(answer.table.rows) == 1


def test_answer_question_table_empty_path(db_session: Session, monkeypatch) -> None:
    _seed_one_game(db_session)
    table_spec = query_engine.TableSpec(
        entity=query_engine.TableEntity.GAMES,
        filters=query_engine.FilterSpec(date_from=datetime.date(2099, 1, 1)),
    )
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(
            status="ok", output="table", table=table_spec
        ),
    )

    answer = assistant.answer_question(db_session, "jogos futuros")

    assert answer.status == "ok"
    assert answer.output == "table"
    assert answer.message is not None
    assert answer.table is not None
    assert answer.table.rows == []


def test_answer_question_table_unresolvable_filter_path(
    db_session: Session, monkeypatch
) -> None:
    table_spec = query_engine.TableSpec(
        entity=query_engine.TableEntity.GAMES,
        filters=query_engine.FilterSpec(team_name="Nonexistent"),
    )
    monkeypatch.setattr(
        llm_query,
        "interpret",
        lambda db, question: llm_query.LLMQueryResponse(
            status="ok", output="table", table=table_spec
        ),
    )

    answer = assistant.answer_question(db_session, "jogos do time inexistente")

    assert answer.status == "error"
    assert answer.output == "table"
