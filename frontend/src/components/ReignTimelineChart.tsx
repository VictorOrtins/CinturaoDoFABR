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
import type { TooltipContentProps } from "recharts";
import { useTheme } from "../theme/theme-context";
import type { ReignTimelineEntry } from "../api/types";
import { FALLBACK_TEAM_COLOR, tooltipContentStyle, tooltipLabelStyle } from "./chartTheme";

interface ReignTimelineChartProps {
  entries: ReignTimelineEntry[];
}

const MS_PER_DAY = 86_400_000;
// Reigns can be as short as a few days on an 18-year axis — without a floor, most
// bars would render sub-pixel and be impossible to see or hover.
const MIN_VISIBLE_DAYS = 45;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR");
}

interface TimelineRow {
  id: string;
  label: string;
  offset: number;
  duration: number;
  color: string;
  range: string;
}

export function ReignTimelineChart({ entries }: ReignTimelineChartProps) {
  const { theme } = useTheme();
  const axisColor = theme === "dark" ? "#97a3b8" : "#6b7280";
  const gridColor = theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(13, 27, 47, 0.12)";

  if (entries.length === 0) return null;

  const minTime = new Date(entries[0].start).getTime();
  const rows: TimelineRow[] = entries.map((entry, index) => {
    const startTime = new Date(entry.start).getTime();
    const endTime = new Date(entry.end).getTime();
    return {
      id: `${entry.team.name}__${index}`,
      label: entry.ongoing ? `${entry.team.name} (atual)` : entry.team.name,
      offset: (startTime - minTime) / MS_PER_DAY,
      duration: Math.max((endTime - startTime) / MS_PER_DAY, MIN_VISIBLE_DAYS),
      color: entry.team.primary_color ?? FALLBACK_TEAM_COLOR,
      range: `${formatDate(entry.start)} – ${entry.ongoing ? "atual" : formatDate(entry.end)}`,
    };
  });
  const labelById = new Map(rows.map((row) => [row.id, row.label]));
  const maxDays = Math.max(...rows.map((row) => row.offset + row.duration));

  function renderTooltip({ active, payload }: TooltipContentProps) {
    if (!active || !payload || payload.length === 0) return null;
    const row = payload.find((item) => item.dataKey === "duration")?.payload as
      | TimelineRow
      | undefined;
    if (!row) return null;
    return (
      <div style={tooltipContentStyle}>
        <p style={tooltipLabelStyle}>{row.label}</p>
        <p>{row.range}</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(320, rows.length * 36)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} horizontal={false} />
        <XAxis
          type="number"
          domain={[0, maxDays]}
          tickFormatter={(value: number) =>
            new Date(minTime + value * MS_PER_DAY).getFullYear().toString()
          }
          tick={{ fill: axisColor }}
        />
        <YAxis
          type="category"
          dataKey="id"
          width={170}
          tick={{ fill: axisColor }}
          tickFormatter={(id: string) => labelById.get(id) ?? id}
        />
        <Tooltip content={renderTooltip} cursor={{ fill: gridColor }} />
        <Bar dataKey="offset" stackId="reign" fill="transparent" legendType="none" />
        <Bar dataKey="duration" stackId="reign" radius={[4, 4, 4, 4]}>
          {rows.map((row) => (
            <Cell key={row.id} fill={row.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
