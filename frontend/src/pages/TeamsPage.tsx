import { useEffect, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Team } from "../api/types";
import { LoadingBelt } from "../components/LoadingBelt";
import { TeamLogo } from "../components/TeamLogo";
import "./TeamsPage.css";

export function TeamsPage() {
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getTeams(true)
      .then(setTeams)
      .catch(() => setError("Não foi possível carregar os times."));
  }, []);

  return (
    <div className="teams-page">
      <h1>Times</h1>
      <p>Todos os times que já disputaram o Cinturão do FABR.</p>

      {error && <p className="teams-page__status">{error}</p>}
      {!error && !teams && <LoadingBelt />}
      {!error && teams && (
        <div className="teams-page__grid">
          {teams.map((team) => (
            <Link
              key={team.id}
              to={`/times/${team.id}`}
              className="team-card"
              style={{ "--team-color": team.primary_color ?? "var(--color-dark-navy)" } as CSSProperties}
            >
              <TeamLogo team={team} size={56} />
              <span className="team-card__name">{team.name}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
