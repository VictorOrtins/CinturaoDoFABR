import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GamesTable } from "../components/GamesTable";
import type { Game, Team } from "../api/types";

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

describe("GamesTable", () => {
  it("renders a row per game with team names and score", () => {
    const home = makeTeam(1, "Brown Spiders");
    const away = makeTeam(2, "Coritiba Crocodiles");
    const game: Game = {
      id: 1,
      date: "2008-10-25T14:00:00",
      home_team: home,
      away_team: away,
      venue: null,
      tournament: "Amistoso",
      phase: null,
      home_score: 33,
      away_score: 10,
      winner_team: home,
      defender_team: null,
    };

    render(<GamesTable games={[game]} />);

    expect(screen.getAllByText("Brown Spiders")).toHaveLength(2); // home team + winner
    expect(screen.getByText("Coritiba Crocodiles")).toBeInTheDocument();
    expect(screen.getByText("33 - 10")).toBeInTheDocument();
  });
});
