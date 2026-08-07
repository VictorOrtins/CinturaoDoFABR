import { Link } from "react-router-dom";
import type { Game, Team } from "../api/types";
import { TeamLogo } from "./TeamLogo";
import "./GamesTable.css";

interface GamesTableProps {
  games: Game[];
}

function TeamLink({ team }: { team: Team }) {
  return (
    <Link to={`/times/${team.id}`} className="games-table__team-link">
      <TeamLogo team={team} size={24} />
      {team.name}
    </Link>
  );
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
            <td>
              <TeamLink team={game.home_team} />
            </td>
            <td>
              {game.home_score ?? "?"} - {game.away_score ?? "?"}
            </td>
            <td>
              <TeamLink team={game.away_team} />
            </td>
            <td>
              {game.tournament ? (
                <span className="chip">{game.tournament}</span>
              ) : (
                "-"
              )}
            </td>
            <td>
              {game.winner_team ? <TeamLink team={game.winner_team} /> : "-"}
            </td>
            <td>
              {game.defender_team ? <TeamLink team={game.defender_team} /> : "-"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
