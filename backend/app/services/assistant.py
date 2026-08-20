import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.services import llm_query, query_engine

logger = logging.getLogger(__name__)

_LLM_ERROR_MESSAGE = "Não consegui processar sua pergunta agora. Tente novamente."
_NO_CHART_DATA_MESSAGE = "Não encontrei jogos que respondam essa pergunta."
_NO_TABLE_ROWS_MESSAGE = "Não encontrei nenhum resultado para essa pergunta."


@dataclass
class AssistantAnswer:
    status: Literal["ok", "unsupported", "error"]
    message: str | None
    output: Literal["chart", "table"]
    chart: query_engine.QueryResult | None = None
    table: query_engine.TableResult | None = None


def _answer_chart(db: Session, spec: query_engine.QuerySpec) -> AssistantAnswer:
    try:
        result = query_engine.execute(db, spec)
    except query_engine.QueryEngineError as exc:
        return AssistantAnswer("error", str(exc), "chart")

    if not result.buckets:
        return AssistantAnswer("ok", _NO_CHART_DATA_MESSAGE, "chart", chart=result)
    return AssistantAnswer("ok", None, "chart", chart=result)


def _answer_table(db: Session, spec: query_engine.TableSpec) -> AssistantAnswer:
    try:
        result = query_engine.execute_table(db, spec)
    except query_engine.QueryEngineError as exc:
        return AssistantAnswer("error", str(exc), "table")

    if not result.rows:
        return AssistantAnswer("ok", _NO_TABLE_ROWS_MESSAGE, "table", table=result)
    return AssistantAnswer("ok", None, "table", table=result)


def answer_question(db: Session, question: str) -> AssistantAnswer:
    try:
        llm_response = llm_query.interpret(db, question)
    except llm_query.AssistantLLMError:
        logger.exception("Failed to interpret assistant question")
        return AssistantAnswer("error", _LLM_ERROR_MESSAGE, "chart")

    if llm_response.status == "unsupported":
        return AssistantAnswer("unsupported", llm_response.reason, llm_response.output)

    if llm_response.output == "table":
        assert llm_response.table is not None
        return _answer_table(db, llm_response.table)

    assert llm_response.spec is not None
    return _answer_chart(db, llm_response.spec)
