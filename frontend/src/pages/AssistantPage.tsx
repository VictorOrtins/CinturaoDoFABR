import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api/client";
import type { AssistantAnswer } from "../api/types";
import { AssistantChartAnswer } from "../components/AssistantChartAnswer";
import { AssistantTable } from "../components/AssistantTable";
import { LoadingBelt } from "../components/LoadingBelt";
import "./AssistantPage.css";

const GENERIC_ERROR = "Não foi possível processar sua pergunta agora. Tente novamente.";

function hasResultData(answer: AssistantAnswer): boolean {
  if (answer.status !== "ok") return false;
  if (answer.output === "table") return (answer.table?.rows.length ?? 0) > 0;
  const { leaderboard, points } = answer.chart ?? {};
  return (leaderboard?.length ?? 0) > 0 || (points?.length ?? 0) > 0;
}

export function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || pending) return;

    setPending(true);
    setAnswer(null);
    try {
      const result = await api.askAssistant(trimmed);
      setAnswer(result);
    } catch {
      setAnswer({ status: "error", message: GENERIC_ERROR, output: "chart", chart: null, table: null });
    } finally {
      setPending(false);
    }
  }

  const showResult = !pending && answer && hasResultData(answer);

  return (
    <div className="assistant-page">
      <h1>Assistente</h1>
      <p>
        Pergunte algo sobre o histórico do Cinturão do FABR e receba um gráfico ou uma
        tabela.
      </p>

      <form className="assistant-page__form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="assistant-page__input"
          placeholder="Ex: quem tem mais defesas de título na região sul?"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          aria-label="Sua pergunta"
        />
        <button type="submit" disabled={pending || !question.trim()}>
          Perguntar
        </button>
      </form>

      <div className="assistant-page__card">
        {pending && <LoadingBelt label="Pensando..." />}
        {!pending && !answer && (
          <p className="assistant-page__status">Faça uma pergunta para ver um resultado.</p>
        )}
        {!pending && answer && !hasResultData(answer) && (
          <p className="assistant-page__status">
            {answer.message ?? "Sem dados para essa pergunta."}
          </p>
        )}
        {showResult && answer.output === "chart" && answer.chart && (
          <>
            <h2>{answer.chart.value_label}</h2>
            <AssistantChartAnswer result={answer.chart} />
          </>
        )}
        {showResult && answer.output === "table" && answer.table && (
          <AssistantTable table={answer.table} />
        )}
      </div>
    </div>
  );
}
