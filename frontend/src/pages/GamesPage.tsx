import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { Game } from "../api/types";
import { GamesTable } from "../components/GamesTable";
import "./GamesPage.css";

export function GamesPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getGames().then(setGames).catch(() => setError("Não foi possível carregar os jogos."));
  }, []);

  const filteredGames = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return games;
    return games.filter(
      (game) =>
        game.home_team.name.toLowerCase().includes(query) ||
        game.away_team.name.toLowerCase().includes(query) ||
        (game.tournament ?? "").toLowerCase().includes(query),
    );
  }, [games, search]);

  return (
    <div className="games-page">
      <h1>Jogos do Cinturão</h1>
      <p>Todos os jogos que valeram o Cinturão do FABR, do primeiro ao mais recente.</p>
      <input
        className="games-page__search"
        type="search"
        placeholder="Buscar por time ou torneio..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      {error && <p>{error}</p>}
      <div className="games-page__table-card">
        <GamesTable games={filteredGames} />
      </div>
    </div>
  );
}
