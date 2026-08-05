import type { Game } from "../api/types";
import { TeamLogo } from "./TeamLogo";
import "./GamesTable.css";

interface GamesTableProps {
  games: Game[];
}

export function GamesTable({ games }: GamesTableProps) {
  return (
    <table className="games-table">
      <thead>
        <tr>
          <th>Data</th>
          <th>Mandante</th>
          <th>Resultado</th>
          <th>Visitante</th>
          <th>Torneio</th>
          <th>Vencedor</th>
          <th>Defensor do Cinturão</th>
        </tr>
      </thead>
      <tbody>
        {games.map((game) => (
          <tr key={game.id}>
            <td>{game.date.slice(0, 10)}</td>
            <td className="games-table__team">
              <TeamLogo team={game.home_team} size={24} />
              {game.home_team.name}
            </td>
            <td>
              {game.home_score ?? "?"} - {game.away_score ?? "?"}
            </td>
            <td className="games-table__team">
              <TeamLogo team={game.away_team} size={24} />
              {game.away_team.name}
            </td>
            <td>{game.tournament ?? "-"}</td>
            <td>{game.winner_team?.name ?? "-"}</td>
            <td>{game.defender_team?.name ?? "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
