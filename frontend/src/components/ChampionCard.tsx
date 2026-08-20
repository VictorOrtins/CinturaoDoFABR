import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import type { CurrentChampion } from "../api/types";
import { getContrastingTextColor, getHardShadowColor } from "../utils/color";
import { TeamLogo } from "./TeamLogo";
import "./ChampionCard.css";

interface ChampionCardProps {
  champion: CurrentChampion;
}

export function ChampionCard({ champion }: ChampionCardProps) {
  const since = new Date(champion.champion_since).toLocaleDateString("pt-BR");
  const bg = champion.team.primary_color ?? "var(--color-dark-navy)";
  const ink = getContrastingTextColor(champion.team.primary_color);
  const shadow = getHardShadowColor(champion.team.primary_color);

  return (
    <div
      className="champion-card halftone"
      style={
        {
          backgroundColor: bg,
          color: ink,
          "--hero-ink": ink,
          "--hero-shadow": shadow,
        } as CSSProperties
      }
    >
      <div className="champion-card__logo-plate">
        <TeamLogo team={champion.team} size={80} />
      </div>
      <Link to={`/times/${champion.team.id}`} className="champion-card__name">
        {champion.team.name}
      </Link>
      <p className="champion-card__since">Detentor do Cinturão desde {since}</p>
    </div>
  );
}
