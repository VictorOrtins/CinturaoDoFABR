import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TitlesByRegionChart } from "../components/TitlesByRegionChart";
import type { RegionCount } from "../api/types";
import { ThemeProvider } from "../theme/ThemeContext";

describe("TitlesByRegionChart", () => {
  it("renders a legend entry with the count for each region", () => {
    const entries: RegionCount[] = [
      { region: "sul", value: 12 },
      { region: "sudeste", value: 5 },
    ];

    render(
      <ThemeProvider>
        <TitlesByRegionChart entries={entries} />
      </ThemeProvider>,
    );

    expect(screen.getByText("Sul — 12")).toBeInTheDocument();
    expect(screen.getByText("Sudeste — 5")).toBeInTheDocument();
  });
});
