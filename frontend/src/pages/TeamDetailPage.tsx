import { useEffect, useState, type CSSProperties } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Game, Team } from "../api/types";
import { LoadingBelt } from "../components/LoadingBelt";
import { TeamLogo } from "../components/TeamLogo";
import { getContrastingTextColor, getHardShadowColor } from "../utils/color";
import "./TeamDetailPage.css";

const REGION_LABELS: Record<string, string> = {
  sul: "Sul",
  sudeste: "Sudeste",
  nordeste: "Nordeste",
  "centro-oeste": "Centro-Oeste",
  norte: "Norte",
};

const RECENT_GAMES_COUNT = 5;

function describeGame(game: Game, teamId: number) {
  const isHome = game.home_team.id === teamId;
  return {
    opponent: isHome ? game.away_team : game.home_team,
    teamScore: isHome ? game.home_score : game.away_score,
    opponentScore: isHome ? game.away_score : game.home_score,
    won: game.winner_team?.id === teamId,
  };
}

export function TeamDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [games, setGames] = useState<Game[] | null>(null);

  useEffect(() => {
    if (!id) return;
    setTeam(null);
    setError(null);
    api
      .getTeam(Number(id))
      .then(setTeam)
      .catch(() => setError("Não foi possível carregar esse time."));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setGames(null);
    api
      .getTeamGames(Number(id))
      .then(setGames)
      .catch(() => setGames([]));
  }, [id]);

  return (
    <div className="team-detail-page">
      <Link to="/times" className="team-detail-page__back">
        ← Times
      </Link>

      {error && <p className="team-detail-page__status">{error}</p>}
      {!error && !team && <LoadingBelt />}
      {!error && team && (
        <>
          <div
            className="team-detail-page__hero halftone"
            style={
              {
                backgroundColor: team.primary_color ?? "var(--color-dark-navy)",
                color: getContrastingTextColor(team.primary_color),
                "--hero-ink": getContrastingTextColor(team.primary_color),
                "--hero-shadow": getHardShadowColor(team.primary_color),
              } as CSSProperties
            }
          >
            <div className="team-detail-page__logo-plate">
              <TeamLogo team={team} size={96} />
            </div>
            <h1 className="team-detail-page__name">{team.name}</h1>
          </div>

          <dl className="team-detail-page__bio">
            <div className="team-detail-page__row">
              <dt>Cidade</dt>
              <dd>{team.home_city ?? "—"}</dd>
            </div>
            <div className="team-detail-page__row">
              <dt>Estado</dt>
              <dd>{team.state ?? "—"}</dd>
            </div>
            <div className="team-detail-page__row">
              <dt>Região</dt>
              <dd>{team.region ? (REGION_LABELS[team.region] ?? team.region) : "—"}</dd>
            </div>
            {team.external_url && (
              <div className="team-detail-page__row">
                <dt>Perfil</dt>
                <dd>
                  <a href={team.external_url} target="_blank" rel="noreferrer">
                    {team.external_url.replace(/^https?:\/\//, "")}
                  </a>
                </dd>
              </div>
            )}
          </dl>

          <div className="team-detail-page__recent">
            <h2>Últimos Jogos do Cinturão</h2>
            {games === null && <LoadingBelt label="Carregando jogos..." />}
            {games !== null && games.length === 0 && (
              <p className="team-detail-page__status">Nenhum jogo encontrado.</p>
            )}
            {games !== null && games.length > 0 && (
              <ul className="recent-games">
                {games
                  .slice(-RECENT_GAMES_COUNT)
                  .reverse()
                  .map((game) => {
                    const { opponent, teamScore, opponentScore, won } = describeGame(
                      game,
                      team.id,
                    );
                    return (
                      <li key={game.id} className="recent-game">
                        <span className="recent-game__date">{game.date.slice(0, 10)}</span>
                        <Link to={`/times/${opponent.id}`} className="recent-game__opponent">
                          <TeamLogo team={opponent} size={20} />
                          {opponent.name}
                        </Link>
                        <span className="recent-game__score">
                          {teamScore ?? "?"}-{opponentScore ?? "?"}
                        </span>
                        <span
                          className={`recent-game__result recent-game__result--${won ? "win" : "loss"}`}
                        >
                          {won ? "V" : "D"}
                        </span>
                      </li>
                    );
                  })}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
