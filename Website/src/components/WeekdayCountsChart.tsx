import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { WeekdayCount } from "../api";
import { useChartTheme } from "../theme/chart";

const DAY_LABELS: Record<string, string> = {
  monday: "Mon",
  tuesday: "Tue",
  wednesday: "Wed",
  thursday: "Thu",
  friday: "Fri",
  saturday: "Sat",
  sunday: "Sun",
};

export default function WeekdayCountsChart({ data }: { data: WeekdayCount[] }) {
  const chart = useChartTheme();
  const chartData = data.map((d) => ({ ...d, label: DAY_LABELS[d.day] ?? d.day }));

  return (
    <div className="panel">
      <h3>Records per weekday file</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid {...chart.grid} />
          <XAxis dataKey="label" {...chart.axis} />
          <YAxis {...chart.axis} />
          <Tooltip
            {...chart.tooltip}
            />
          <Bar isAnimationActive={chart.animate} dataKey="records" fill={chart.colours.accent} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
