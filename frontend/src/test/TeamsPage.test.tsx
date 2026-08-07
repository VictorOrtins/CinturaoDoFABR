import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import type { Team } from "../api/types";

const mockApi = { getTeams: vi.fn() };
vi.mock("../api/client", () => ({ api: mockApi }));

const { TeamsPage } = await import("../pages/TeamsPage");

function makeTeam(id: number, name: string): Team {
  return {
    id,
    name,
    logo_url: null,
    home_city: null,
    primary_color: "#123456",
    external_url: null,
    state: null,
    region: null,
  };
}

describe("TeamsPage", () => {
  it("renders a link to each team's detail page", async () => {
    mockApi.getTeams.mockResolvedValue([makeTeam(1, "Brown Spiders"), makeTeam(2, "Recife Mariners")]);

    render(
      <MemoryRouter>
        <TeamsPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("Brown Spiders")).toBeInTheDocument());
    expect(mockApi.getTeams).toHaveBeenCalledWith(true);
    expect(screen.getByRole("link", { name: /Brown Spiders/ })).toHaveAttribute(
      "href",
      "/times/1",
    );
    expect(screen.getByRole("link", { name: /Recife Mariners/ })).toHaveAttribute(
      "href",
      "/times/2",
    );
  });
});
