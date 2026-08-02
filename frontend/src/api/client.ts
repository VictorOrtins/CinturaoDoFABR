import type { CurrentChampion, Game, Team } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getTeams: () => get<Team[]>("/api/teams"),
  getGames: () => get<Game[]>("/api/games"),
  getCurrentChampion: () => get<CurrentChampion>("/api/cinturao/current"),
};
