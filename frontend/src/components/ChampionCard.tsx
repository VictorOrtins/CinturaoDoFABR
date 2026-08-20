import { Link } from "react-router-dom";
import type { CurrentChampion } from "../api/types";
import { TeamLogo } from "./TeamLogo";
import "./ChampionCard.css";

interface ChampionCardProps {
  champion: CurrentChampion;
}

export function ChampionCard({ champion }: ChampionCardProps) {
  const since = new Date(champion.champion_since).toLocaleDateString("pt-BR");

  return (
    <div
      className="champion-card"
      style={{ borderColor: champion.team.primary_color ?? "var(--color-accent-yellow)" }}
    >
      <TeamLogo team={champion.team} size={96} />
      <Link to={`/times/${champion.team.id}`} className="champion-card__name">
        {champion.team.name}
      </Link>
      <p className="champion-card__since">Detentor do Cinturão desde {since}</p>
    </div>
  );
}
