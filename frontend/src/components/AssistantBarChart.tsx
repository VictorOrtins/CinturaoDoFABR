import type { AssistantPoint } from "../api/types";
import { LabeledBarChart } from "./LabeledBarChart";

interface AssistantBarChartProps {
  points: AssistantPoint[];
  valueLabel: string;
}

export function AssistantBarChart({ points, valueLabel }: AssistantBarChartProps) {
  return <LabeledBarChart data={points} xKey="label" valueLabel={valueLabel} />;
}
