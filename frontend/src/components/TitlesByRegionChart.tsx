import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "../theme/theme-context";
import type { RegionCount } from "../api/types";
import { tooltipContentStyle, tooltipLabelStyle } from "./chartTheme";
import "./TitlesByRegionChart.css";

interface TitlesByRegionChartProps {
  entries: RegionCount[];
}

// Regions aren't teams, so they have no brand color of their own — this is the
// dataviz skill's validated 5-slot categorical palette (blue/orange/aqua/yellow/
// magenta), checked against this app's actual light and dark chart surfaces.
const REGION_COLORS_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"];
const REGION_COLORS_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"];

const REGION_LABELS: Record<string, string> = {
  sul: "Sul",
  sudeste: "Sudeste",
  nordeste: "Nordeste",
  "centro-oeste": "Centro-Oeste",
  norte: "Norte",
};

function regionLabel(region: string): string {
  return REGION_LABELS[region] ?? region;
}

export function TitlesByRegionChart({ entries }: TitlesByRegionChartProps) {
  const { theme } = useTheme();
  const colors = theme === "dark" ? REGION_COLORS_DARK : REGION_COLORS_LIGHT;
  const total = entries.reduce((sum, entry) => sum + entry.value, 0);
  const row: Record<string, number | string> = { name: "Conquistas" };
  entries.forEach((entry) => {
    row[entry.region] = entry.value;
  });

  return (
    <div>
      <ResponsiveContainer width="100%" height={110}>
        <BarChart data={[row]} layout="vertical" margin={{ top: 8, bottom: 8 }}>
          <XAxis type="number" hide domain={[0, total]} />
          <YAxis type="category" dataKey="name" hide />
          <Tooltip
            contentStyle={tooltipContentStyle}
            labelStyle={tooltipLabelStyle}
            formatter={(value, region) => [value, regionLabel(String(region))]}
          />
          {entries.map((entry, index) => (
            <Bar
              key={entry.region}
              dataKey={entry.region}
              stackId="regions"
              fill={colors[index % colors.length]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <ul className="region-legend">
        {entries.map((entry, index) => (
          <li key={entry.region}>
            <span
              className="region-legend__swatch"
              style={{ backgroundColor: colors[index % colors.length] }}
            />
            {regionLabel(entry.region)} — {entry.value}
          </li>
        ))}
      </ul>
    </div>
  );
}
