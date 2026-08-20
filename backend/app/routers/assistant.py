from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import (
    AssistantAnswerOut,
    AssistantLeaderboardEntryOut,
    AssistantPointOut,
    AssistantQueryResultOut,
    AssistantQuestionIn,
    AssistantTableOut,
)
from app.services import assistant as assistant_service
from app.services.query_engine import QueryResult, TableResult

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def _chart_out(result: QueryResult | None) -> AssistantQueryResultOut | None:
    if result is None:
        return None
    if result.chart_type == "leaderboard":
        leaderboard = [
            AssistantLeaderboardEntryOut.model_validate(bucket)
            for bucket in result.buckets
        ]
        return AssistantQueryResultOut(
            chart_type=result.chart_type,
            value_label=result.value_label,
            leaderboard=leaderboard,
        )
    points = [
        AssistantPointOut(label=bucket.label, value=bucket.value)
        for bucket in result.buckets
    ]
    return AssistantQueryResultOut(
        chart_type=result.chart_type,
        value_label=result.value_label,
        points=points,
    )


def _table_out(result: TableResult | None) -> AssistantTableOut | None:
    if result is None:
        return None
    return AssistantTableOut(columns=result.columns, rows=result.rows)


@router.post("/query", response_model=AssistantAnswerOut)
def post_query(
    payload: AssistantQuestionIn, db: Session = Depends(get_db)
) -> AssistantAnswerOut:
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=503, detail="Assistente de IA não configurado."
        )

    answer = assistant_service.answer_question(db, payload.question)
    return AssistantAnswerOut(
        status=answer.status,
        message=answer.message,
        output=answer.output,
        chart=_chart_out(answer.chart),
        table=_table_out(answer.table),
    )
