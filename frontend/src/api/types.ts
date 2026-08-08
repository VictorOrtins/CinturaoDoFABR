export interface Team {
  id: number;
  name: string;
  logo_url: string | null;
  home_city: string | null;
  primary_color: string | null;
  external_url: string | null;
  state: string | null;
  region: string | null;
}

export interface Game {
  id: number;
  date: string;
  home_team: Team;
  away_team: Team;
  venue: string | null;
  tournament: string | null;
  phase: string | null;
  home_score: number | null;
  away_score: number | null;
  winner_team: Team | null;
  defender_team: Team | null;
}

export interface CurrentChampion {
  team: Team;
  champion_since: string;
}

export interface LeaderboardEntry {
  team: Team;
  value: number;
}

export interface ReignTimelineEntry {
  team: Team;
  start: string;
  end: string;
  ongoing: boolean;
}

export interface RegionCount {
  region: string;
  value: number;
}

export interface YearCount {
  year: number;
  value: number;
}

export interface MarginBucketCount {
  bucket: string;
  value: number;
}

export type AssistantChartType = "leaderboard" | "bar" | "line";

export interface AssistantPoint {
  label: string;
  value: number;
}

export interface AssistantQueryResult {
  chart_type: AssistantChartType;
  value_label: string;
  leaderboard: LeaderboardEntry[] | null;
  points: AssistantPoint[] | null;
}

export interface AssistantTable {
  columns: string[];
  rows: Record<string, string>[];
}

export interface AssistantAnswer {
  status: "ok" | "unsupported" | "error";
  message: string | null;
  output: "chart" | "table";
  chart: AssistantQueryResult | null;
  table: AssistantTable | null;
}
