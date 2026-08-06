import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReignTimelineChart } from "../components/ReignTimelineChart";
import type { ReignTimelineEntry, Team } from "../api/types";
import { ThemeProvider } from "../theme/ThemeContext";

function makeTeam(id: number, name: string): Team {
  return {
    id,
    name,
    logo_url: null,
    home_city: null,
    primary_color: null,
    external_url: null,
    state: null,
    region: null,
  };
}

describe("ReignTimelineChart", () => {
  it("renders one bar per reign period", () => {
    const entries: ReignTimelineEntry[] = [
      {
        team: makeTeam(1, "Brown Spiders"),
        start: "2008-10-25T00:00:00",
        end: "2009-08-22T00:00:00",
        ongoing: false,
      },
      {
        team: makeTeam(2, "Coritiba Crocodiles"),
        start: "2009-08-22T00:00:00",
        end: "2020-01-01T00:00:00",
        ongoing: true,
      },
    ];

    const { container } = render(
      <ThemeProvider>
        <ReignTimelineChart entries={entries} />
      </ThemeProvider>,
    );

    // Each period stacks two bars (an invisible offset + the visible duration), but
    // a zero-length offset (the very first period, which starts at day 0) renders no
    // rectangle at all — so this is a floor, not an exact count.
    expect(
      container.querySelectorAll(".recharts-bar-rectangle").length,
    ).toBeGreaterThanOrEqual(entries.length);
  });

  it("renders nothing for an empty timeline", () => {
    const { container } = render(
      <ThemeProvider>
        <ReignTimelineChart entries={[]} />
      </ThemeProvider>,
    );

    expect(container.querySelector(".recharts-wrapper")).not.toBeInTheDocument();
  });
});
