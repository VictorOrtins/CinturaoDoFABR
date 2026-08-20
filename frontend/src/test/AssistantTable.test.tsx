import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssistantTable } from "../components/AssistantTable";
import type { AssistantTable as AssistantTableData } from "../api/types";

describe("AssistantTable", () => {
  it("renders one header per column and one row per entry", () => {
    const table: AssistantTableData = {
      columns: ["Data", "Mandante", "Visitante"],
      rows: [
        { Data: "2020-01-01", Mandante: "Team A", Visitante: "Team B" },
        { Data: "2020-02-01", Mandante: "Team B", Visitante: "Team A" },
      ],
    };

    render(<AssistantTable table={table} />);

    expect(screen.getByRole("columnheader", { name: "Data" })).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(3); // header + 2 rows
    expect(screen.getByText("2020-01-01")).toBeInTheDocument();
  });
});
