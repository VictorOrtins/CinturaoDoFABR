import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTheme } from "../theme/theme-context";
import type { LeaderboardEntry } from "../api/types";
import { FALLBACK_TEAM_COLOR, tooltipContentStyle, tooltipLabelStyle } from "./chartTheme";

interface LeaderboardChartProps {
  entries: LeaderboardEntry[];
  valueLabel: string;
}

export function LeaderboardChart({ entries, valueLabel }: LeaderboardChartProps) {
  const { theme } = useTheme();
  const axisColor = theme === "dark" ? "#97a3b8" : "#6b7280";
  const gridColor = theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(13, 27, 47, 0.12)";

  const data = entries.map((entry) => ({
    team: entry.team.name,
    value: entry.value,
    color: entry.team.primary_color ?? FALLBACK_TEAM_COLOR,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(280, data.length * 40)}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis type="number" allowDecimals={false} tick={{ fill: axisColor }} />
        <YAxis type="category" dataKey="team" width={160} tick={{ fill: axisColor }} />
        <Tooltip
          contentStyle={tooltipContentStyle}
          labelStyle={tooltipLabelStyle}
          formatter={(value) => [value, valueLabel]}
          cursor={{ fill: gridColor }}
        />
        <Bar dataKey="value" name={valueLabel}>
          {data.map((entry) => (
            <Cell key={entry.team} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
