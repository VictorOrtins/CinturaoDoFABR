import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LeaderboardChart } from "../components/LeaderboardChart";
import type { LeaderboardEntry, Team } from "../api/types";
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

describe("LeaderboardChart", () => {
  it("renders one bar per leaderboard entry", () => {
    const entries: LeaderboardEntry[] = [
      { team: makeTeam(1, "Brown Spiders"), value: 8 },
      { team: makeTeam(2, "Coritiba Crocodiles"), value: 5 },
    ];

    const { container } = render(
      <ThemeProvider>
        <LeaderboardChart entries={entries} valueLabel="Defesas" />
      </ThemeProvider>,
    );

    expect(container.querySelectorAll(".recharts-bar-rectangle")).toHaveLength(entries.length);
  });
});
