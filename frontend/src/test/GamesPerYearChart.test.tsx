import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GamesPerYearChart } from "../components/GamesPerYearChart";
import type { YearCount } from "../api/types";
import { ThemeProvider } from "../theme/ThemeContext";

describe("GamesPerYearChart", () => {
  it("renders an area/line series for the given years", () => {
    const entries: YearCount[] = [
      { year: 2019, value: 3 },
      { year: 2020, value: 5 },
    ];

    const { container } = render(
      <ThemeProvider>
        <GamesPerYearChart entries={entries} valueLabel="Jogos" />
      </ThemeProvider>,
    );

    expect(container.querySelector(".recharts-area")).toBeInTheDocument();
  });
});
