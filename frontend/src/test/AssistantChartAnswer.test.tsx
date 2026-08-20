import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { AssistantQueryResult } from "../api/types";

vi.mock("../components/LeaderboardChart", () => ({
  LeaderboardChart: () => <div data-testid="leaderboard-chart" />,
}));
vi.mock("../components/AssistantBarChart", () => ({
  AssistantBarChart: () => <div data-testid="bar-chart" />,
}));
vi.mock("../components/AssistantLineChart", () => ({
  AssistantLineChart: () => <div data-testid="line-chart" />,
}));

const { AssistantChartAnswer } = await import("../components/AssistantChartAnswer");

function baseResult(overrides: Partial<AssistantQueryResult>): AssistantQueryResult {
  return {
    chart_type: "bar",
    value_label: "Jogos",
    leaderboard: null,
    points: null,
    ...overrides,
  };
}

describe("AssistantChartAnswer", () => {
  it("renders LeaderboardChart for chart_type leaderboard", () => {
    render(
      <AssistantChartAnswer
        result={baseResult({ chart_type: "leaderboard", leaderboard: [] })}
      />,
    );
    expect(screen.getByTestId("leaderboard-chart")).toBeInTheDocument();
  });

  it("renders AssistantBarChart for chart_type bar", () => {
    render(<AssistantChartAnswer result={baseResult({ chart_type: "bar", points: [] })} />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("renders AssistantLineChart for chart_type line", () => {
    render(<AssistantChartAnswer result={baseResult({ chart_type: "line", points: [] })} />);
    expect(screen.getByTestId("line-chart")).toBeInTheDocument();
  });
});
