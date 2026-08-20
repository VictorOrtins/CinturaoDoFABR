import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssistantLineChart } from "../components/AssistantLineChart";
import type { AssistantPoint } from "../api/types";
import { ThemeProvider } from "../theme/ThemeContext";

describe("AssistantLineChart", () => {
  it("renders an area/line series for the given points", () => {
    const points: AssistantPoint[] = [
      { label: "2019", value: 3 },
      { label: "2020", value: 5 },
    ];

    const { container } = render(
      <ThemeProvider>
        <AssistantLineChart points={points} valueLabel="Jogos" />
      </ThemeProvider>,
    );

    expect(container.querySelector(".recharts-area")).toBeInTheDocument();
  });
});
