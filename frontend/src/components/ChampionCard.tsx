import type { CurrentChampion } from "../api/types";
import { TeamLogo } from "./TeamLogo";
import "./ChampionCard.css";

interface ChampionCardProps {
  champion: CurrentChampion;
}

export function ChampionCard({ champion }: ChampionCardProps) {
  const since = new Date(champion.champion_since).toLocaleDateString("pt-BR");

  return (
    <div className="champion-card">
      <TeamLogo team={champion.team} size={96} />
      <h2 className="champion-card__name">{champion.team.name}</h2>
      <p className="champion-card__since">Detentor do Cinturão desde {since}</p>
    </div>
  );
}
