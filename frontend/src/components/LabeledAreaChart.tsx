import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "../theme/theme-context";
import { tooltipContentStyle, tooltipLabelStyle } from "./chartTheme";

interface LabeledAreaChartProps<T> {
  data: T[];
  xKey: keyof T & string;
  valueLabel: string;
}

export function LabeledAreaChart<T extends { value: number }>({
  data,
  xKey,
  valueLabel,
}: LabeledAreaChartProps<T>) {
  const { theme } = useTheme();
  const axisColor = theme === "dark" ? "#a89e8f" : "#7a7168";
  const gridColor = theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(23, 19, 16, 0.14)";
  const lineColor = theme === "dark" ? "#7fa0c2" : "#5b7a99";

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
        <XAxis dataKey={(entry: T) => entry[xKey]} tick={{ fill: axisColor }} />
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
