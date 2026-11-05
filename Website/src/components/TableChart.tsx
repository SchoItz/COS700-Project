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
import type { Table } from "../api";
import { useNarrow } from "../hooks/useNarrow";
import { formatScore, useChartTheme } from "../theme/chart";
import { HorizontalBars } from "./Charts";

/** Charts a strategy table from the raw values carried on each row, so the
 * bars and the table above them always describe the same numbers. Returns
 * nothing for tables that are not per-strategy comparisons. */
export default function TableChart({ table }: { table: Table }) {
  const chart = useChartTheme();
  const narrow = useNarrow();
  const rows = table.sections.flatMap((s) => s.rows).filter((r) => r.key && r.key !== "mean");
  if (rows.length === 0) return null;
  const sample = rows[0].values;

  if ("importance" in sample) {
    // Signal importance: the per-signal section, largest first.
    const signals = table.sections[0].rows.map((r) => ({ signal: r.label.text.charAt(0).toUpperCase() + r.label.text.slice(1), importance: r.values.importance }));
    return (
      <HorizontalBars
        data={signals}
        category="signal"
        series={[{ key: "importance", label: "Importance" }]}
        labelWidth={230}
      />
    );
  }

  let series: { key: string; label: string }[];
  if ("f1" in sample && "precision" in sample) {
    // Per-strategy results table.
    series = [
      { key: "precision", label: "Precision" },
      { key: "recall", label: "Recall" },
      { key: "f1", label: "F1" },
    ];
  } else {
    // Strategy x variant table: one F1 bar per variant, named by the header.
    const variants = Object.keys(sample).filter((k) => k.endsWith(".f1"));
    if (variants.length === 0) return null;
    const names = table.header[0].slice(1).map((h) => h.text);
    series = variants.map((key, i) => ({ key, label: `${names[i] ?? key} F1` }));
  }

  const data = rows.map((r) => ({
    strategy: r.label.text,
    ...Object.fromEntries(series.map((s) => [s.label, r.values[s.key]])),
  }));

  // Phones: fifteen strategies do not fit side by side, so list them as rows.
  if (narrow) {
    return (
      <HorizontalBars
        data={data}
        category="strategy"
        series={series.map((s) => ({ key: s.label, label: s.label }))}
        domain={[0, 1]}
        labels={false}
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 56 }}>
        <CartesianGrid {...chart.grid} />
        <XAxis
          dataKey="strategy"
          {...chart.axis}
          angle={-35}
          textAnchor="end"
          interval={0}
          height={80}
          tick={{ ...chart.axis.tick, fontSize: 11 }}
        />
        <YAxis {...chart.axis} domain={[0, 1]} />
        <Tooltip
            {...chart.tooltip}
            formatter={formatScore}
        />
        <Legend
          verticalAlign="top"
          itemSorter={() => 0}
          formatter={(v) => <span style={{ color: chart.colours.text }}>{v}</span>}
          {...chart.legend}
        />
        {series.map((s, i) => (
          <Bar key={s.key} isAnimationActive={chart.animate} dataKey={s.label} fill={chart.series[i % chart.series.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
