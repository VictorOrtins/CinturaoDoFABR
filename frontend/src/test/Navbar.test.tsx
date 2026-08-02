import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Navbar } from "../components/Navbar";

describe("Navbar", () => {
  it("renders a link to every main page", () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Início" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Jogos" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Regras" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Estatísticas" })).toBeInTheDocument();
  });
});
