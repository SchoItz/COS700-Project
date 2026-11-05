import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchDriftTrend, type DriftTrendRow } from "../api";
import { useChartTheme } from "../theme/chart";

const METRICS = [
  "device_activity_count",
  "print_activity_count",
  "file_activity_count",
  "failed_login_count",
  "data_transfer_mb",
  "session_duration_minutes",
];
const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

export default function DriftTrendChart() {
  const chart = useChartTheme();
  const [metric, setMetric] = useState(METRICS[0]);
  const [day, setDay] = useState(DAYS[0]);
  const [data, setData] = useState<DriftTrendRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchDriftTrend(metric, day)
      .then(setData)
      .finally(() => setLoading(false));
  }, [metric, day]);

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Behaviour drift over time</h3>
        <div className="panel-controls">
          <select value={day} onChange={(e) => setDay(e.target.value)}>
            {DAYS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>
            {METRICS.map((m) => (
              <option key={m} value={m}>
                {m.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>
      </div>
      {loading ? (
        <div className="loading">Loading…</div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 16 }}>
            <CartesianGrid {...chart.grid} />
            <XAxis dataKey="week_number" {...chart.axis} label={{ value: "Week", position: "insideBottom", offset: -2, fill: chart.colours.muted }} />
            <YAxis {...chart.axis} />
            <Tooltip
            {...chart.tooltip}
            />
            <Legend verticalAlign="top" {...chart.legend} />
            <Line isAnimationActive={chart.animate} type="monotone" dataKey="benign" stroke={chart.colours.good} dot={false} strokeWidth={2} />
            <Line isAnimationActive={chart.animate} type="monotone" dataKey="drifted" stroke={chart.colours.bad} dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
