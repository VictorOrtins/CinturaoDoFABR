import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";
import { ThemeProvider } from "../theme/ThemeContext";

describe("Sidebar", () => {
  it("renders a link to every main page", () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <Sidebar />
        </ThemeProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Início" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Jogos" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Regras" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Estatísticas" })).toBeInTheDocument();
  });

  it("renders a theme toggle button", () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <Sidebar />
        </ThemeProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: /modo/i })).toBeInTheDocument();
  });
});
