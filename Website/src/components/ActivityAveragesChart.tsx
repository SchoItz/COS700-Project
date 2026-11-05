import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ActivityAverageRow } from "../api";
import { useChartTheme } from "../theme/chart";

const METRICS = [
  "device_activity_count",
  "print_activity_count",
  "email_activity_count",
  "file_activity_count",
  "http_activity_count",
  "failed_login_count",
  "data_transfer_mb",
  "session_duration_minutes",
];

export default function ActivityAveragesChart({ data }: { data: ActivityAverageRow[] }) {
  const chart = useChartTheme();
  const [metric, setMetric] = useState(METRICS[0]);

  const chartData = useMemo(() => {
    const byDay: Record<string, { day: string; benign?: number; drifted?: number }> = {};
    for (const row of data) {
      byDay[row.day] ??= { day: row.day };
      byDay[row.day][row.group] = row[metric] as number;
    }
    return Object.values(byDay);
  }, [data, metric]);

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Average activity: benign vs drifted</h3>
        <select value={metric} onChange={(e) => setMetric(e.target.value)}>
          {METRICS.map((m) => (
            <option key={m} value={m}>
              {m.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid {...chart.grid} />
          <XAxis dataKey="day" {...chart.axis} />
          <YAxis {...chart.axis} />
          <Tooltip
            {...chart.tooltip}
            />
          <Legend {...chart.legend} />
          <Bar isAnimationActive={chart.animate} dataKey="benign" fill={chart.colours.good} radius={[4, 4, 0, 0]} />
          <Bar isAnimationActive={chart.animate} dataKey="drifted" fill={chart.colours.bad} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
