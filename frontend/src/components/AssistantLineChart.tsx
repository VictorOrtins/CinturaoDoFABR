import type { AssistantPoint } from "../api/types";
import { LabeledAreaChart } from "./LabeledAreaChart";

interface AssistantLineChartProps {
  points: AssistantPoint[];
  valueLabel: string;
}

export function AssistantLineChart({ points, valueLabel }: AssistantLineChartProps) {
  return <LabeledAreaChart data={points} xKey="label" valueLabel={valueLabel} />;
}
