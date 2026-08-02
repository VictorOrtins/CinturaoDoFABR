import type { Team } from "../api/types";

interface TeamLogoProps {
  team: Team;
  size?: number;
}

export function TeamLogo({ team, size = 32 }: TeamLogoProps) {
  if (!team.logo_url) {
    return <span style={{ width: size, height: size, display: "inline-block" }} />;
  }
  return (
    <img
      src={team.logo_url}
      alt={team.name}
      width={size}
      height={size}
      style={{ objectFit: "contain" }}
    />
  );
}
