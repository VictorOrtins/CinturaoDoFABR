import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  LeaderboardEntry,
  MarginBucketCount,
  RegionCount,
  ReignTimelineEntry,
  YearCount,
} from "../api/types";
import { GamesPerYearChart } from "../components/GamesPerYearChart";
import { LeaderboardChart } from "../components/LeaderboardChart";
import { ReignTimelineChart } from "../components/ReignTimelineChart";
import { ScoreMarginHistogram } from "../components/ScoreMarginHistogram";
import { TitlesByRegionChart } from "../components/TitlesByRegionChart";
import "./StatsPage.css";

type StatDefinition =
  | {
      key: string;
      label: string;
      kind: "leaderboard";
      valueLabel: string;
      fetch: () => Promise<LeaderboardEntry[]>;
    }
  | { key: string; label: string; kind: "timeline"; fetch: () => Promise<ReignTimelineEntry[]> }
  | { key: string; label: string; kind: "region"; fetch: () => Promise<RegionCount[]> }
  | {
      key: string;
      label: string;
      kind: "trend";
      valueLabel: string;
      fetch: () => Promise<YearCount[]>;
    }
  | {
      key: string;
      label: string;
      kind: "histogram";
      valueLabel: string;
      fetch: () => Promise<MarginBucketCount[]>;
    };

type StatData =
  | LeaderboardEntry[]
  | ReignTimelineEntry[]
  | RegionCount[]
  | YearCount[]
  | MarginBucketCount[];

const STATS: StatDefinition[] = [
  {
    key: "reign-timeline",
    label: "Linha do tempo do cinturão",
    kind: "timeline",
    fetch: api.getReignTimeline,
  },
  {
    key: "title-defenses",
    label: "Times com mais defesas de título",
    kind: "leaderboard",
    valueLabel: "Defesas",
    fetch: api.getTitleDefenses,
  },
  {
    key: "title-wins",
    label: "Times com mais conquistas do cinturão",
    kind: "leaderboard",
    valueLabel: "Conquistas",
    fetch: api.getTitleWins,
  },
  {
    key: "most-games",
    label: "Times que mais jogaram jogos valendo o cinturão",
    kind: "leaderboard",
    valueLabel: "Jogos",
    fetch: api.getMostGamesPlayed,
  },
  {
    key: "most-losses",
    label: "Times que mais perderam jogos valendo o cinturão",
    kind: "leaderboard",
    valueLabel: "Derrotas",
    fetch: api.getMostGameLosses,
  },
  {
    key: "title-losses",
    label: "Times com mais perdas do cinturão",
    kind: "leaderboard",
    valueLabel: "Perdas",
    fetch: api.getTitleLosses,
  },
  {
    key: "days-with-title",
    label: "Times que mais tempo ficaram com o cinturão (Total)",
    kind: "leaderboard",
    valueLabel: "Dias",
    fetch: api.getDaysWithTitle,
  },
  {
    key: "longest-reign",
    label: "Reinado mais longo com o cinturão",
    kind: "leaderboard",
    valueLabel: "Dias",
    fetch: api.getLongestReign,
  },
  {
    key: "longest-win-streak",
    label: "Maior sequência de vitórias com o cinturão",
    kind: "leaderboard",
    valueLabel: "Vitórias seguidas",
    fetch: api.getLongestWinStreak,
  },
  {
    key: "titles-by-region",
    label: "Conquistas do cinturão por região",
    kind: "region",
    fetch: api.getTitlesByRegion,
  },
  {
    key: "games-per-year",
    label: "Jogos valendo o cinturão por ano",
    kind: "trend",
    valueLabel: "Jogos",
    fetch: api.getGamesPerYear,
  },
  {
    key: "score-margin",
    label: "Distribuição da diferença de pontos nos jogos",
    kind: "histogram",
    valueLabel: "Jogos",
    fetch: api.getScoreMarginDistribution,
  },
];

function renderChart(stat: StatDefinition, data: StatData) {
  switch (stat.kind) {
    case "leaderboard":
      return <LeaderboardChart entries={data as LeaderboardEntry[]} valueLabel={stat.valueLabel} />;
    case "timeline":
      return <ReignTimelineChart entries={data as ReignTimelineEntry[]} />;
    case "region":
      return <TitlesByRegionChart entries={data as RegionCount[]} />;
    case "trend":
      return <GamesPerYearChart entries={data as YearCount[]} valueLabel={stat.valueLabel} />;
    case "histogram":
      return <ScoreMarginHistogram entries={data as MarginBucketCount[]} valueLabel={stat.valueLabel} />;
  }
}

export function StatsPage() {
  const [selectedKey, setSelectedKey] = useState(STATS[0].key);
  const [data, setData] = useState<StatData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedStat = STATS.find((stat) => stat.key === selectedKey) ?? STATS[0];

  useEffect(() => {
    let cancelled = false;
    const stat = STATS.find((candidate) => candidate.key === selectedKey) ?? STATS[0];
    setData(null);
    setError(null);
    stat
      .fetch()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar essa estatística.");
      });
    return () => {
      cancelled = true;
    };
  }, [selectedKey]);

  return (
    <div className="stats-page">
      <h1>Estatísticas</h1>
      <p>Estatísticas dos times que já disputaram o Cinturão do FABR.</p>

      <select
        className="stats-page__select"
        value={selectedKey}
        onChange={(event) => setSelectedKey(event.target.value)}
        aria-label="Escolha uma estatística"
      >
        {STATS.map((stat) => (
          <option key={stat.key} value={stat.key}>
            {stat.label}
          </option>
        ))}
      </select>

      <div className="stats-page__card">
        <h2>{selectedStat.label}</h2>
        {error && <p className="stats-page__status">{error}</p>}
        {!error && !data && <p className="stats-page__status">Carregando...</p>}
        {!error && data && data.length === 0 && (
          <p className="stats-page__status">Ainda não há dados suficientes para essa estatística.</p>
        )}
        {!error && data && data.length > 0 && renderChart(selectedStat, data)}
      </div>
    </div>
  );
}
