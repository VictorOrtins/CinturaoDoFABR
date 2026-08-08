import type {
  AssistantAnswer,
  CurrentChampion,
  Game,
  LeaderboardEntry,
  MarginBucketCount,
  RegionCount,
  ReignTimelineEntry,
  Team,
  YearCount,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getTeams: (playedOnly = false) =>
    get<Team[]>(`/api/teams${playedOnly ? "?played=true" : ""}`),
  getTeam: (id: number) => get<Team>(`/api/teams/${id}`),
  getTeamGames: (id: number) => get<Game[]>(`/api/teams/${id}/games`),
  getGames: () => get<Game[]>("/api/games"),
  getCurrentChampion: () => get<CurrentChampion>("/api/cinturao/current"),
  getTitleDefenses: () => get<LeaderboardEntry[]>("/api/stats/title-defenses"),
  getTitleWins: () => get<LeaderboardEntry[]>("/api/stats/title-wins"),
  getMostGamesPlayed: () => get<LeaderboardEntry[]>("/api/stats/most-games"),
  getMostGameLosses: () => get<LeaderboardEntry[]>("/api/stats/most-losses"),
  getTitleLosses: () => get<LeaderboardEntry[]>("/api/stats/title-losses"),
  getDaysWithTitle: () => get<LeaderboardEntry[]>("/api/stats/days-with-title"),
  getLongestReign: () => get<LeaderboardEntry[]>("/api/stats/longest-reign"),
  getLongestWinStreak: () => get<LeaderboardEntry[]>("/api/stats/longest-win-streak"),
  getReignTimeline: () => get<ReignTimelineEntry[]>("/api/stats/reign-timeline"),
  getTitlesByRegion: () => get<RegionCount[]>("/api/stats/titles-by-region"),
  getGamesPerYear: () => get<YearCount[]>("/api/stats/games-per-year"),
  getScoreMarginDistribution: () =>
    get<MarginBucketCount[]>("/api/stats/score-margin-distribution"),
  askAssistant: (question: string) =>
    post<AssistantAnswer>("/api/assistant/query", { question }),
};
