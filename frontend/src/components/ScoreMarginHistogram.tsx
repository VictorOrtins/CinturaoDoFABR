import type { MarginBucketCount } from "../api/types";
import { LabeledBarChart } from "./LabeledBarChart";

interface ScoreMarginHistogramProps {
  entries: MarginBucketCount[];
  valueLabel: string;
}

export function ScoreMarginHistogram({ entries, valueLabel }: ScoreMarginHistogramProps) {
  return <LabeledBarChart data={entries} xKey="bucket" valueLabel={valueLabel} />;
}
