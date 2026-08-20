import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "../theme/theme-context";
import { tooltipContentStyle, tooltipLabelStyle } from "./chartTheme";

interface LabeledBarChartProps<T> {
  data: T[];
  xKey: keyof T & string;
  valueLabel: string;
}

export function LabeledBarChart<T extends { value: number }>({
  data,
  xKey,
  valueLabel,
}: LabeledBarChartProps<T>) {
  const { theme } = useTheme();
  const axisColor = theme === "dark" ? "#a89e8f" : "#7a7168";
  const gridColor = theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(23, 19, 16, 0.14)";
  const barColor = theme === "dark" ? "#e0574c" : "#b3261e";

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
        <XAxis dataKey={(entry: T) => entry[xKey]} tick={{ fill: axisColor }} />
        <YAxis allowDecimals={false} tick={{ fill: axisColor }} width={32} />
        <Tooltip
          contentStyle={tooltipContentStyle}
          labelStyle={tooltipLabelStyle}
          formatter={(value) => [value, valueLabel]}
          cursor={{ fill: gridColor }}
        />
        <Bar dataKey="value" name={valueLabel} fill={barColor} radius={[4, 4, 0, 0]} maxBarSize={24} />
      </BarChart>
    </ResponsiveContainer>
  );
}
