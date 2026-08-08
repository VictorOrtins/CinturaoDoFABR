import type { YearCount } from "../api/types";
import { LabeledAreaChart } from "./LabeledAreaChart";

interface GamesPerYearChartProps {
  entries: YearCount[];
  valueLabel: string;
}

export function GamesPerYearChart({ entries, valueLabel }: GamesPerYearChartProps) {
  return <LabeledAreaChart data={entries} xKey="year" valueLabel={valueLabel} />;
}
