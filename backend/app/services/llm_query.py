from typing import Literal

from litellm import completion
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.config import settings
from app.services import query_engine
from app.services.query_engine import QuerySpec, TableSpec

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

_SYSTEM_PROMPT_TEMPLATE = """\
Você traduz perguntas em português sobre o histórico do Cinturão do FABR (um \
"cinturão" de futebol americano brasileiro, disputado entre times em jogos de \
título) em uma consulta estruturada sobre os dados disponíveis.

Os dados disponíveis são APENAS jogos de título (games) e times (teams). Não há \
dados de jogadores, outros esportes, previsões futuras, opiniões ou qualquer \
coisa fora desse escopo. Se a pergunta não puder ser respondida com esses dados, \
responda com status="unsupported" e uma explicação curta em "reason".

Caso contrário, responda com status="ok" e escolha um "output":

- output="chart": para perguntas que pedem uma métrica agregada/comparação (quem \
tem mais X, quantos jogos por ano, média de Y por time). Preencha "spec" (deixe \
"table" nulo) com os seguintes campos:

- group_by: "team" (agrupar por time), "region" (agrupar por região do time) ou \
"year" (agrupar por ano do jogo).
- team_role (obrigatório se group_by for "team" ou "region"): qual papel do time \
no jogo considerar — "home" (mandante — use este para perguntas sobre ONDE os \
jogos aconteceram, ex: "jogos jogados em cada região", já que o mandante sedia o \
jogo), "away" (visitante), "participant" (mandante OU visitante contam — CUIDADO: \
se os dois times de um jogo forem de grupos diferentes [ex: regiões diferentes], \
esse único jogo é somado nos dois grupos, então a soma total pode ficar MAIOR que \
o número real de jogos; só use "participant" quando a pergunta for claramente \
sobre "times de X participaram de quantos jogos", não sobre contar jogos únicos), \
"winner" (vencedor do jogo), "defender" (quem estava defendendo o cinturão; o \
primeiro jogo da história não tem defensor e não conta para esse papel), "loser" \
(quem perdeu o jogo).
- outcome_filter (opcional): "belt_changed_hands" (o cinturão trocou de dono \
nesse jogo) ou "belt_retained" (o cinturão permaneceu com o mesmo dono).
- metric_field: "games" (contar jogos), "score_margin" (diferença de pontos no \
jogo), "points_scored" (pontos marcados pelo time, requer team_role) ou \
"points_allowed" (pontos sofridos pelo time, requer team_role).
- aggregation: "count" (só válido com metric_field="games"), "sum", "avg", "max" \
ou "min" (só válidos com metric_field diferente de "games").
- filters: objeto opcional com team_name, region, state (use um dos \
nomes/valores conhecidos abaixo), date_from e date_to (formato AAAA-MM-DD).
- limit: número máximo de times/regiões a retornar (padrão 10, máximo 10).

- output="table": para perguntas que pedem uma LISTA de jogos ou times, não uma \
métrica agregada — ex: "quais jogos o [time] jogou", "quais times são de São \
Paulo". Preencha "table" (deixe "spec" nulo) com os seguintes campos:

- entity: "games" (listar jogos) ou "teams" (listar times).
- filters: mesmo formato do "spec" acima (team_name, region, state, date_from, \
date_to) — para "quais jogos o [time] jogou" use entity="games" com \
filters.team_name; para "times de [estado/região]" use entity="teams" com \
filters.state ou filters.region.
- limit: número máximo de linhas a retornar (padrão 25, máximo 100).

Não existe um filtro por cor de time — se a pergunta pedir isso (ex: "times \
vermelhos"), responda com status="unsupported".

Times conhecidos: {team_names}
Regiões conhecidas: {regions}
Estados conhecidos: {states}

Exemplos:
Pergunta: "quem tem mais defesas de título na região sul"
Resposta: {{"status": "ok", "spec": {{"group_by": "team", "team_role": \
"defender", "metric_field": "games", "aggregation": "count", "filters": \
{{"region": "sul"}}}}}}

Pergunta: "jogos por ano de times do RS"
Resposta: {{"status": "ok", "spec": {{"group_by": "year", "team_role": \
"participant", "metric_field": "games", "aggregation": "count", "filters": \
{{"state": "RS"}}}}}}

Pergunta: "quantos jogos foram jogados em cada região"
Resposta: {{"status": "ok", "spec": {{"group_by": "region", "team_role": \
"home", "metric_field": "games", "aggregation": "count"}}}}

Pergunta: "qual foi a maior vitória (maior diferença de pontos) de cada time"
Resposta: {{"status": "ok", "spec": {{"group_by": "team", "team_role": \
"winner", "metric_field": "score_margin", "aggregation": "max"}}}}

Pergunta: "quais jogos o Espectros jogou pelo cinturão"
Resposta: {{"status": "ok", "output": "table", "table": {{"entity": "games", \
"filters": {{"team_name": "Espectros"}}}}}}

Pergunta: "quais times são de São Paulo"
Resposta: {{"status": "ok", "output": "table", "table": {{"entity": "teams", \
"filters": {{"state": "SP"}}}}}}

Pergunta: "qual jogador fez mais touchdowns"
Resposta: {{"status": "unsupported", "reason": "Não temos dados no nível de \
jogador, apenas de times e jogos."}}
"""


class LLMQueryResponse(BaseModel):
    status: Literal["ok", "unsupported"]
    reason: str | None = Field(default=None, max_length=200)
    output: Literal["chart", "table"] = "chart"
    spec: QuerySpec | None = None
    table: TableSpec | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> "LLMQueryResponse":
        if self.status == "unsupported":
            if not self.reason:
                raise ValueError("reason is required when status is unsupported")
            return self
        if self.output == "chart" and self.spec is None:
            raise ValueError("spec is required when status is ok and output is chart")
        if self.output == "table" and self.table is None:
            raise ValueError("table is required when status is ok and output is table")
        return self


class AssistantLLMError(Exception):
    """Raised when the LLM call fails or its output can't be interpreted."""


def build_prompt(
    question: str, team_names: list[str], regions: list[str], states: list[str]
) -> list[dict[str, str]]:
    system = _SYSTEM_PROMPT_TEMPLATE.format(
        team_names=", ".join(team_names),
        regions=", ".join(regions),
        states=", ".join(states),
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]


def _call_llm(messages: list[dict[str, str]]) -> LLMQueryResponse:
    try:
        response = completion(
            model=MODEL,
            messages=messages,
            response_format=LLMQueryResponse,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
            api_key=settings.openrouter_api_key,
        )
        content = response.choices[0].message.content
        return LLMQueryResponse.model_validate_json(content)
    except Exception as exc:
        raise AssistantLLMError(str(exc)) from exc


def interpret(db: Session, question: str) -> LLMQueryResponse:
    messages = build_prompt(
        question,
        team_names=query_engine.known_team_names(db),
        regions=query_engine.known_regions(db),
        states=query_engine.known_states(db),
    )
    return _call_llm(messages)
