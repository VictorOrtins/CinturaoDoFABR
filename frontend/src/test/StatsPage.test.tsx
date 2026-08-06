import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeProvider } from "../theme/ThemeContext";

const mockApi = {
  getTitleDefenses: vi.fn(),
  getTitleWins: vi.fn(),
  getMostGamesPlayed: vi.fn(),
  getMostGameLosses: vi.fn(),
  getTitleLosses: vi.fn(),
  getDaysWithTitle: vi.fn(),
  getLongestReign: vi.fn(),
  getLongestWinStreak: vi.fn(),
  getReignTimeline: vi.fn(),
  getTitlesByRegion: vi.fn(),
  getGamesPerYear: vi.fn(),
  getScoreMarginDistribution: vi.fn(),
};

vi.mock("../api/client", () => ({ api: mockApi }));

function mockChart(name: string) {
  return { [name]: ({ entries }: { entries: unknown[] }) => (
    <div data-testid="stat-chart">{entries.length} entradas</div>
  ) };
}
vi.mock("../components/LeaderboardChart", () => mockChart("LeaderboardChart"));
vi.mock("../components/ReignTimelineChart", () => mockChart("ReignTimelineChart"));
vi.mock("../components/TitlesByRegionChart", () => mockChart("TitlesByRegionChart"));
vi.mock("../components/GamesPerYearChart", () => mockChart("GamesPerYearChart"));
vi.mock("../components/ScoreMarginHistogram", () => mockChart("ScoreMarginHistogram"));

const { StatsPage } = await import("../pages/StatsPage");

function renderStatsPage() {
  return render(
    <ThemeProvider>
      <StatsPage />
    </ThemeProvider>,
  );
}

describe("StatsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads the first stat on mount and renders its chart", async () => {
    mockApi.getReignTimeline.mockResolvedValue([
      {
        team: { id: 1, name: "Brown Spiders", logo_url: null, home_city: null, primary_color: null, external_url: null, state: null, region: null },
        start: "2008-10-25T00:00:00",
        end: "2009-08-22T00:00:00",
        ongoing: false,
      },
    ]);

    renderStatsPage();

    expect(screen.getByText("Carregando...")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("stat-chart")).toBeInTheDocument());
    expect(mockApi.getReignTimeline).toHaveBeenCalledTimes(1);
  });

  it("fetches the newly selected stat when the selector changes", async () => {
    mockApi.getReignTimeline.mockResolvedValue([]);
    mockApi.getTitleWins.mockResolvedValue([]);

    renderStatsPage();
    await waitFor(() => expect(mockApi.getReignTimeline).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByLabelText("Escolha uma estatística"), {
      target: { value: "title-wins" },
    });

    await waitFor(() => expect(mockApi.getTitleWins).toHaveBeenCalledTimes(1));
  });

  it("shows an error message when the request fails", async () => {
    mockApi.getReignTimeline.mockRejectedValue(new Error("boom"));

    renderStatsPage();

    expect(
      await screen.findByText("Não foi possível carregar essa estatística."),
    ).toBeInTheDocument();
  });
});
