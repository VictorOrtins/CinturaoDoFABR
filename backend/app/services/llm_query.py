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

## Vocabulário de campos (usado em group_by, sort_by e filters)

Um campo ("field") é {{"entity": ..., "column": ..., "transform": ...}}:

- entity="team": um atributo de um TIME. column pode ser "name" (nome), \
"region" (região), "state" (estado) ou "home_city" (cidade sede). Sempre que \
usar um campo entity="team" em group_by (fora de metric_field="teams") você \
também precisa preencher "team_role" no nível do spec, dizendo QUAL time do \
jogo esse campo se refere.
- entity="game": um atributo do JOGO em si. column pode ser "date" (data), \
"venue" (local), "tournament" (nome do torneio/campeonato daquele jogo — cada \
edição anual é um valor diferente, ex: "Campeonato Catarinense 2011"), "phase" \
(fase do torneio, ex: semifinal/final) "home_score" ou "away_score" (placar do \
mandante/visitante). Não precisa de team_role.
- transform: "identity" (valor bruto, padrão), "initial" (só para colunas de \
texto — primeira letra, maiúscula, ex: nome do time começa com "M"), "year" \
"decade" ou "month" (só para column="date" — ano, década ou mês do jogo).

Não existe campo de cor de time — se a pergunta pedir isso (ex: "times \
vermelhos"), responda com status="unsupported".

## output="chart"

Para perguntas que pedem uma métrica agregada/comparação (quem tem mais X, \
quantos jogos por ano, média de Y por time, quantos TIMES existem em cada \
região/letra). Preencha "spec" (deixe "table" nulo) com:

- group_by: um field (veja acima). Ex: agrupar por região = \
{{"entity":"team","column":"region"}}; agrupar por ano do jogo = \
{{"entity":"game","column":"date","transform":"year"}}; agrupar por letra \
inicial do nome do time = {{"entity":"team","column":"name",\
"transform":"initial"}}.
- team_role (obrigatório sempre que group_by ou algum filtro relevante usar \
entity="team", EXCETO quando metric_field="teams"): qual papel do time no jogo \
considerar — "home" (mandante — use para perguntas sobre ONDE os jogos \
aconteceram, já que o mandante sedia o jogo), "away" (visitante), \
"participant" (mandante OU visitante contam — CUIDADO: se os dois times de um \
jogo tiverem valores diferentes para o campo agrupado [ex: regiões \
diferentes], esse único jogo é somado nos dois grupos, então a soma total pode \
ficar MAIOR que o número real de jogos; só use "participant" quando a \
pergunta for claramente sobre "times de X participaram de quantos jogos", não \
sobre contar jogos únicos), "winner" (vencedor), "defender" (quem estava \
defendendo o cinturão; o primeiro jogo da história não tem defensor), "loser" \
(quem perdeu).
- outcome_filter (opcional, não se aplica com metric_field="teams"): \
"belt_changed_hands" (o cinturão trocou de dono nesse jogo) ou "belt_retained" \
(o cinturão permaneceu com o mesmo dono).
- metric_field: "games" (contar jogos — usa aggregation="count"), "teams" \
(contar TIMES distintos, não jogos — usa aggregation="count"; use isso para \
perguntas do tipo "quantos times..." ou "qual grupo tem mais times", NÃO \
quantos jogos; quando usar metric_field="teams", group_by TEM que ser \
entity="team", team_role/outcome_filter devem ficar vazios, e filtros só podem \
usar entity="team"), "score_margin" (diferença de pontos no jogo), \
"points_scored" (pontos marcados pelo time, requer team_role) ou \
"points_allowed" (pontos sofridos pelo time, requer team_role).
- aggregation: "count" (só com metric_field="games" ou "teams"), "sum", "avg", \
"max" ou "min" (só com os outros metric_field).
- filters: lista de cláusulas {{"field": <field>, "op": "equals"|"gte"|"lte", \
"value": "<texto>"}}. "equals" funciona para qualquer campo; "gte"/"lte" só \
para campos numéricos ou de data (ex: date_from/date_to viram \
{{"field":{{"entity":"game","column":"date"}}, "op":"gte", "value":"2020-01-01"}}). \
Datas em formato AAAA-MM-DD.
- sort_by ("value" ou "key") e direction ("asc" ou "desc"): opcionais, use só \
quando a pergunta pedir uma ordem específica que não seja o padrão (padrão já \
é "mais alto primeiro" para rankings e "cronológico" para série temporal por \
ano). Ex: "os 5 times com MENOS defesas" => sort_by="value", direction="asc".
- limit: número máximo de grupos a retornar (padrão 10, máximo 10).

## output="table"

Para perguntas que pedem uma LISTA de jogos ou times, não uma métrica agregada \
— ex: "quais jogos o [time] jogou", "quais times são de São Paulo", "últimos 5 \
jogos". Preencha "table" (deixe "spec" nulo) com:

- entity: "games" (listar jogos) ou "teams" (listar times).
- filters: mesmo formato de cima, mas campos entity="game" só valem para \
entity="games" (não fazem sentido para uma lista de times).
- sort_by (opcional): um field — para entity="games" tem que ser entity="game" \
(normalmente {{"entity":"game","column":"date"}}); para entity="teams" tem que \
ser entity="team". Se omitido, jogos vêm em ordem cronológica crescente e \
times em ordem alfabética.
- direction: "asc" (padrão) ou "desc". Para "últimos N jogos" / "jogos mais \
recentes", use sort_by na data do jogo com direction="desc".
- limit: número máximo de linhas (padrão 25, máximo 100).

Times conhecidos: {team_names}
Regiões conhecidas: {regions}
Estados conhecidos: {states}
Torneios conhecidos: {tournaments}
Locais conhecidos: {venues}
Fases conhecidas: {phases}

Exemplos:
Pergunta: "quem tem mais defesas de título na região sul"
Resposta: {{"status": "ok", "spec": {{"group_by": {{"entity":"team",\
"column":"name"}}, "team_role": "defender", "metric_field": "games", \
"aggregation": "count", "filters": [{{"field":{{"entity":"team",\
"column":"region"}}, "op":"equals", "value":"sul"}}]}}}}

Pergunta: "jogos por ano de times do RS"
Resposta: {{"status": "ok", "spec": {{"group_by": {{"entity":"game",\
"column":"date","transform":"year"}}, "team_role": "participant", \
"metric_field": "games", "aggregation": "count", "filters": \
[{{"field":{{"entity":"team","column":"state"}}, "op":"equals", \
"value":"RS"}}]}}}}

Pergunta: "quantos jogos foram jogados em cada região"
Resposta: {{"status": "ok", "spec": {{"group_by": {{"entity":"team",\
"column":"region"}}, "team_role": "home", "metric_field": "games", \
"aggregation": "count"}}}}

Pergunta: "qual letra inicial teve mais times disputando o cinturão"
Resposta: {{"status": "ok", "spec": {{"group_by": {{"entity":"team",\
"column":"name","transform":"initial"}}, "metric_field": "teams", \
"aggregation": "count"}}}}

Pergunta: "quantos times cada região tem"
Resposta: {{"status": "ok", "spec": {{"group_by": {{"entity":"team",\
"column":"region"}}, "metric_field": "teams", "aggregation": "count"}}}}

Pergunta: "qual foi a maior vitória (maior diferença de pontos) de cada time"
Resposta: {{"status": "ok", "spec": {{"group_by": {{"entity":"team",\
"column":"name"}}, "team_role": "winner", "metric_field": "score_margin", \
"aggregation": "max"}}}}

Pergunta: "quais jogos o Espectros jogou pelo cinturão"
Resposta: {{"status": "ok", "output": "table", "table": {{"entity": "games", \
"filters": [{{"field":{{"entity":"team","column":"name"}}, "op":"equals", \
"value":"Espectros"}}]}}}}

Pergunta: "quais times são de São Paulo"
Resposta: {{"status": "ok", "output": "table", "table": {{"entity": "teams", \
"filters": [{{"field":{{"entity":"team","column":"state"}}, "op":"equals", \
"value":"SP"}}]}}}}

Pergunta: "quais foram os últimos 5 jogos do cinturão"
Resposta: {{"status": "ok", "output": "table", "table": {{"entity": "games", \
"sort_by": {{"entity":"game","column":"date"}}, "direction": "desc", \
"limit": 5}}}}

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
    question: str,
    team_names: list[str],
    regions: list[str],
    states: list[str],
    tournaments: list[str],
    venues: list[str],
    phases: list[str],
) -> list[dict[str, str]]:
    system = _SYSTEM_PROMPT_TEMPLATE.format(
        team_names=", ".join(team_names),
        regions=", ".join(regions),
        states=", ".join(states),
        tournaments=", ".join(tournaments),
        venues=", ".join(venues),
        phases=", ".join(phases),
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
        tournaments=query_engine.known_tournaments(db),
        venues=query_engine.known_venues(db),
        phases=query_engine.known_phases(db),
    )
    return _call_llm(messages)
