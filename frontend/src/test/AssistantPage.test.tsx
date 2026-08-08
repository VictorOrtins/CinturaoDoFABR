import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeProvider } from "../theme/ThemeContext";

const mockApi = {
  askAssistant: vi.fn(),
};

vi.mock("../api/client", () => ({ api: mockApi }));
vi.mock("../components/AssistantChartAnswer", () => ({
  AssistantChartAnswer: () => <div data-testid="assistant-chart" />,
}));
vi.mock("../components/AssistantTable", () => ({
  AssistantTable: ({ table }: { table: { rows: unknown[] } }) => (
    <div data-testid="assistant-table">{table.rows.length} linhas</div>
  ),
}));

const { AssistantPage } = await import("../pages/AssistantPage");

function renderAssistantPage() {
  return render(
    <ThemeProvider>
      <AssistantPage />
    </ThemeProvider>,
  );
}

async function ask(question: string) {
  fireEvent.change(screen.getByLabelText("Sua pergunta"), { target: { value: question } });
  fireEvent.click(screen.getByRole("button", { name: "Perguntar" }));
}

describe("AssistantPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a prompt before any question is asked", () => {
    renderAssistantPage();
    expect(screen.getByText("Faça uma pergunta para ver um resultado.")).toBeInTheDocument();
  });

  it("renders a chart when the assistant answers with chart data", async () => {
    mockApi.askAssistant.mockResolvedValue({
      status: "ok",
      message: null,
      output: "chart",
      chart: {
        chart_type: "leaderboard",
        value_label: "Defesas",
        leaderboard: [
          {
            team: {
              id: 1,
              name: "Team A",
              logo_url: null,
              home_city: null,
              primary_color: null,
              external_url: null,
              state: null,
              region: null,
            },
            value: 5,
          },
        ],
        points: null,
      },
      table: null,
    });

    renderAssistantPage();
    await ask("quem tem mais defesas");

    expect(await screen.findByTestId("assistant-chart")).toBeInTheDocument();
    expect(mockApi.askAssistant).toHaveBeenCalledWith("quem tem mais defesas");
  });

  it("renders a table when the assistant answers with table data", async () => {
    mockApi.askAssistant.mockResolvedValue({
      status: "ok",
      message: null,
      output: "table",
      chart: null,
      table: {
        columns: ["Data", "Mandante", "Visitante", "Placar", "Campeão"],
        rows: [
          {
            Data: "2020-01-01",
            Mandante: "Team A",
            Visitante: "Team B",
            Placar: "20 x 17",
            Campeão: "Team A",
          },
        ],
      },
    });

    renderAssistantPage();
    await ask("quais jogos o Team A jogou");

    expect(await screen.findByTestId("assistant-table")).toBeInTheDocument();
  });

  it("shows the assistant's message when the question is unsupported", async () => {
    mockApi.askAssistant.mockResolvedValue({
      status: "unsupported",
      message: "Não temos dados de jogadores.",
      output: "chart",
      chart: null,
      table: null,
    });

    renderAssistantPage();
    await ask("qual jogador fez mais touchdowns");

    expect(await screen.findByText("Não temos dados de jogadores.")).toBeInTheDocument();
  });

  it("shows a generic error message when the request fails", async () => {
    mockApi.askAssistant.mockRejectedValue(new Error("boom"));

    renderAssistantPage();
    await ask("quem tem mais defesas");

    expect(
      await screen.findByText("Não foi possível processar sua pergunta agora. Tente novamente."),
    ).toBeInTheDocument();
  });

  it("does not submit an empty question", () => {
    renderAssistantPage();
    expect(screen.getByRole("button", { name: "Perguntar" })).toBeDisabled();
    expect(mockApi.askAssistant).not.toHaveBeenCalled();
  });
});
