import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreMarginHistogram } from "../components/ScoreMarginHistogram";
import type { MarginBucketCount } from "../api/types";
import { ThemeProvider } from "../theme/ThemeContext";

describe("ScoreMarginHistogram", () => {
  it("renders one bar per margin bucket", () => {
    const entries: MarginBucketCount[] = [
      { bucket: "1-5", value: 4 },
      { bucket: "6-10", value: 2 },
    ];

    const { container } = render(
      <ThemeProvider>
        <ScoreMarginHistogram entries={entries} valueLabel="Jogos" />
      </ThemeProvider>,
    );

    expect(container.querySelectorAll(".recharts-bar-rectangle")).toHaveLength(entries.length);
  });
});
