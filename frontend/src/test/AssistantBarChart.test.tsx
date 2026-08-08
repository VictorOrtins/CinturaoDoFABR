import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssistantBarChart } from "../components/AssistantBarChart";
import type { AssistantPoint } from "../api/types";
import { ThemeProvider } from "../theme/ThemeContext";

describe("AssistantBarChart", () => {
  it("renders one bar per point", () => {
    const points: AssistantPoint[] = [
      { label: "sul", value: 4 },
      { label: "sudeste", value: 2 },
    ];

    const { container } = render(
      <ThemeProvider>
        <AssistantBarChart points={points} valueLabel="Jogos" />
      </ThemeProvider>,
    );

    expect(container.querySelectorAll(".recharts-bar-rectangle")).toHaveLength(points.length);
  });
});
