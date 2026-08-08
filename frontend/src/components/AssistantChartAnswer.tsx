import type { AssistantQueryResult } from "../api/types";
import { AssistantBarChart } from "./AssistantBarChart";
import { AssistantLineChart } from "./AssistantLineChart";
import { LeaderboardChart } from "./LeaderboardChart";

interface AssistantChartAnswerProps {
  result: AssistantQueryResult;
}

export function AssistantChartAnswer({ result }: AssistantChartAnswerProps) {
  switch (result.chart_type) {
    case "leaderboard":
      return (
        <LeaderboardChart entries={result.leaderboard ?? []} valueLabel={result.value_label} />
      );
    case "bar":
      return <AssistantBarChart points={result.points ?? []} valueLabel={result.value_label} />;
    case "line":
      return <AssistantLineChart points={result.points ?? []} valueLabel={result.value_label} />;
  }
}
