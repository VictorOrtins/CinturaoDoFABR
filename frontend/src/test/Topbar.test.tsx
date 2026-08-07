import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Topbar } from "../components/Topbar";
import { ThemeProvider } from "../theme/ThemeContext";

describe("Topbar", () => {
  it("renders a link to every main page", () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <Topbar />
        </ThemeProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Início" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Jogos" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Times" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Regras" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Estatísticas" })).toBeInTheDocument();
  });

  it("renders a theme toggle button", () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <Topbar />
        </ThemeProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: /modo/i })).toBeInTheDocument();
  });
});
