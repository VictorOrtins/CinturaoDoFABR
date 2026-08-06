import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "../theme/theme-context";
import type { YearCount } from "../api/types";
import { tooltipContentStyle, tooltipLabelStyle } from "./chartTheme";

interface GamesPerYearChartProps {
  entries: YearCount[];
  valueLabel: string;
}

export function GamesPerYearChart({ entries, valueLabel }: GamesPerYearChartProps) {
  const { theme } = useTheme();
  const axisColor = theme === "dark" ? "#97a3b8" : "#6b7280";
  const gridColor = theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(13, 27, 47, 0.12)";
  const lineColor = theme === "dark" ? "#4db8ea" : "#209dd7";

  const data = entries.map((entry) => ({ year: entry.year, value: entry.value }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
        <XAxis dataKey="year" tick={{ fill: axisColor }} />
        <YAxis allowDecimals={false} tick={{ fill: axisColor }} width={32} />
        <Tooltip
          contentStyle={tooltipContentStyle}
          labelStyle={tooltipLabelStyle}
          formatter={(value) => [value, valueLabel]}
        />
        <Area
          type="monotone"
          dataKey="value"
          name={valueLabel}
          stroke={lineColor}
          strokeWidth={2}
          fill={lineColor}
          fillOpacity={0.1}
          dot={{ r: 4, fill: lineColor }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
