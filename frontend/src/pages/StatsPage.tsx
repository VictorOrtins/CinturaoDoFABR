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
import { LoadingBelt } from "../components/LoadingBelt";
import { ReignTimelineChart } from "../components/ReignTimelineChart";
import { ScoreMarginHistogram } from "../components/ScoreMarginHistogram";
import { TitlesByRegionChart } from "../components/TitlesByRegionChart";
import "./StatsPage.css";

type StatGroup = "Linha do tempo" | "Rankings de times" | "Tendências";

type StatDefinition =
  | {
      key: string;
      label: string;
      group: StatGroup;
      kind: "leaderboard";
      valueLabel: string;
      fetch: () => Promise<LeaderboardEntry[]>;
    }
  | {
      key: string;
      label: string;
      group: StatGroup;
      kind: "timeline";
      fetch: () => Promise<ReignTimelineEntry[]>;
    }
  | {
      key: string;
      label: string;
      group: StatGroup;
      kind: "region";
      fetch: () => Promise<RegionCount[]>;
    }
  | {
      key: string;
      label: string;
      group: StatGroup;
      kind: "trend";
      valueLabel: string;
      fetch: () => Promise<YearCount[]>;
    }
  | {
      key: string;
      label: string;
      group: StatGroup;
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
    group: "Linha do tempo",
    kind: "timeline",
    fetch: api.getReignTimeline,
  },
  {
    key: "title-defenses",
    label: "Times com mais defesas de título",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Defesas",
    fetch: api.getTitleDefenses,
  },
  {
    key: "title-wins",
    label: "Times com mais conquistas do cinturão",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Conquistas",
    fetch: api.getTitleWins,
  },
  {
    key: "most-games",
    label: "Times que mais jogaram jogos valendo o cinturão",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Jogos",
    fetch: api.getMostGamesPlayed,
  },
  {
    key: "most-losses",
    label: "Times que mais perderam jogos valendo o cinturão",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Derrotas",
    fetch: api.getMostGameLosses,
  },
  {
    key: "title-losses",
    label: "Times com mais perdas do cinturão",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Perdas",
    fetch: api.getTitleLosses,
  },
  {
    key: "days-with-title",
    label: "Times que mais tempo ficaram com o cinturão (Total)",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Dias",
    fetch: api.getDaysWithTitle,
  },
  {
    key: "longest-reign",
    label: "Reinado mais longo com o cinturão",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Dias",
    fetch: api.getLongestReign,
  },
  {
    key: "longest-win-streak",
    label: "Maior sequência de vitórias com o cinturão",
    group: "Rankings de times",
    kind: "leaderboard",
    valueLabel: "Vitórias seguidas",
    fetch: api.getLongestWinStreak,
  },
  {
    key: "titles-by-region",
    label: "Conquistas do cinturão por região",
    group: "Tendências",
    kind: "region",
    fetch: api.getTitlesByRegion,
  },
  {
    key: "games-per-year",
    label: "Jogos valendo o cinturão por ano",
    group: "Tendências",
    kind: "trend",
    valueLabel: "Jogos",
    fetch: api.getGamesPerYear,
  },
  {
    key: "score-margin",
    label: "Distribuição da diferença de pontos nos jogos",
    group: "Tendências",
    kind: "histogram",
    valueLabel: "Jogos",
    fetch: api.getScoreMarginDistribution,
  },
];

const STAT_GROUPS: StatGroup[] = ["Linha do tempo", "Rankings de times", "Tendências"];

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

      <div className="stats-page__select-wrap">
        <select
          className="stats-page__select"
          value={selectedKey}
          onChange={(event) => setSelectedKey(event.target.value)}
          aria-label="Escolha uma estatística"
        >
          {STAT_GROUPS.map((group) => (
            <optgroup key={group} label={group}>
              {STATS.filter((stat) => stat.group === group).map((stat) => (
                <option key={stat.key} value={stat.key}>
                  {stat.label}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      <div className="stats-page__card">
        <h2>{selectedStat.label}</h2>
        {error && <p className="stats-page__status">{error}</p>}
        {!error && !data && <LoadingBelt />}
        {!error && data && data.length === 0 && (
          <p className="stats-page__status">Ainda não há dados suficientes para essa estatística.</p>
        )}
        {!error && data && data.length > 0 && renderChart(selectedStat, data)}
      </div>
    </div>
  );
}
