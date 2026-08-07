import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { Game, Team } from "../api/types";

const mockApi = { getTeam: vi.fn(), getTeamGames: vi.fn() };
vi.mock("../api/client", () => ({ api: mockApi }));

const { TeamDetailPage } = await import("../pages/TeamDetailPage");

function makeTeam(id: number, name: string): Team {
  return {
    id,
    name,
    logo_url: null,
    home_city: "Curitiba/PR",
    primary_color: "#1e1818",
    external_url: "https://www.salaooval.com.br/times/brown-spiders/",
    state: "PR",
    region: "sul",
  };
}

function renderTeamDetail(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/times/${id}`]}>
      <Routes>
        <Route path="/times/:id" element={<TeamDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TeamDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the team's hero and bio rows once loaded", async () => {
    mockApi.getTeam.mockResolvedValue(makeTeam(1, "Brown Spiders"));
    mockApi.getTeamGames.mockResolvedValue([]);

    renderTeamDetail("1");

    await waitFor(() => expect(screen.getByText("Brown Spiders")).toBeInTheDocument());
    expect(mockApi.getTeam).toHaveBeenCalledWith(1);
    expect(screen.getByText("Curitiba/PR")).toBeInTheDocument();
    expect(screen.getByText("Sul")).toBeInTheDocument();
  });

  it("shows an error message when the team request fails", async () => {
    mockApi.getTeam.mockRejectedValue(new Error("boom"));
    mockApi.getTeamGames.mockResolvedValue([]);

    renderTeamDetail("1");

    expect(await screen.findByText("Não foi possível carregar esse time.")).toBeInTheDocument();
  });

  it("renders the team's recent games with opponent and result", async () => {
    const team = makeTeam(1, "Brown Spiders");
    const opponent = makeTeam(2, "Coritiba Crocodiles");
    const game: Game = {
      id: 1,
      date: "2009-08-22T14:00:00",
      home_team: team,
      away_team: opponent,
      venue: null,
      tournament: "Torneio Touchdown 2009",
      phase: null,
      home_score: 20,
      away_score: 23,
      winner_team: opponent,
      defender_team: team,
    };
    mockApi.getTeam.mockResolvedValue(team);
    mockApi.getTeamGames.mockResolvedValue([game]);

    renderTeamDetail("1");

    await waitFor(() => expect(mockApi.getTeamGames).toHaveBeenCalledWith(1));
    expect(await screen.findByText("Coritiba Crocodiles")).toBeInTheDocument();
    expect(screen.getByText("20-23")).toBeInTheDocument();
    expect(screen.getByText("D")).toBeInTheDocument();
  });
});
