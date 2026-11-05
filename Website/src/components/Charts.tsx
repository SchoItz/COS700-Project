/** Small, reusable charts built on the site's chart theme (theme/chart.ts).
 * Every chart gets a hover tooltip; charts with two or more series get a
 * legend; values are printed on the bars when there are few enough to read. */
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useNarrow } from "../hooks/useNarrow";
import { formatScore, useChartTheme } from "../theme/chart";

export interface Series {
  key: string;
  label: string;
}

type Datum = Record<string, string | number | null>;

interface BarProps {
  data: Datum[];
  /** Field holding the category name of each row. */
  category: string;
  series: Series[];
  height?: number;
  /** Fixed value range, e.g. [0, 1] for scores. Omit to fit the data. */
  domain?: [number, number];
  format?: (v: number) => string;
  /** Print the value on each bar (default: on, when there are at most 12 bars). */
  labels?: boolean;
  /** Fixed colour slot per series (index into the palette), so an entity keeps
   * its colour across charts. Defaults to series order. */
  slots?: number[];
  /** Hide the value axis (when every bar is labelled, as on the poster). */
  hideValueAxis?: boolean;
  /** Format the value axis ticks with `format` too (e.g. percentages). */
  formatAxis?: boolean;
  /** Explicit bar colours, one per series (overrides the palette slots). */
  colors?: string[];
  /** Poster style, as on the A1 poster: square bars and legend keys, no grid,
   * smaller axis labels. Text colours still follow the theme. */
  paper?: boolean;
}

/** Vertical grouped bars: one group per category, one bar per series. */
export function GroupedBars({
  data,
  category,
  series,
  height = 260,
  domain,
  format = (v) => formatScore(v),
  labels,
  slots,
  hideValueAxis,
  formatAxis,
  colors,
  paper,
}: BarProps) {
  const t = useChartTheme();
  const showLabels = labels ?? data.length * series.length <= 12;
  const ink = { text: t.colours.text, muted: t.colours.muted, border: t.colours.border };
  const axis = paper ? { stroke: ink.border, tick: { fill: ink.text, fontSize: 11 } } : t.axis;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        margin={{ top: showLabels ? 22 : 8, right: 8, left: hideValueAxis ? 8 : 0, bottom: 4 }}
        barGap={paper ? 1 : 2}
        barCategoryGap={series.length > 2 ? "10%" : "22%"}
      >
        {!paper && <CartesianGrid {...t.grid} />}
        <XAxis dataKey={category} {...axis} interval={0} tickLine={!paper} />
        <YAxis
          {...axis}
          domain={domain ?? [0, "auto"]}
          hide={hideValueAxis}
          width={44}
          tickFormatter={formatAxis ? (v: number) => format(v) : undefined}
        />
        <Tooltip {...t.tooltip} formatter={(v) => (typeof v === "number" ? format(v) : String(v))} />
        {series.length > 1 && (
          <Legend
            verticalAlign="bottom"
            iconType={paper ? "square" : "circle"}
            iconSize={paper ? 9 : undefined}
            itemSorter={() => 0}
            formatter={(v) => <span style={{ color: ink.text }}>{v}</span>}
            {...t.legend}
          />
        )}
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            fill={colors?.[i] ?? t.series[(slots?.[i] ?? i) % t.series.length]}
            radius={paper ? 0 : [4, 4, 0, 0]}
            maxBarSize={paper ? 70 : 56}
            isAnimationActive={t.animate}
          >
            {showLabels && (
              <LabelList
                dataKey={s.key}
                position="top"
                formatter={(v: unknown) => (typeof v === "number" ? format(v) : "")}
                style={{ fill: ink.text, fontSize: series.length > 2 ? 10 : 11, fontWeight: 700 }}
              />
            )}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Horizontal bars for long category names (signals, strategies), sorted as given. */
export function HorizontalBars({
  data,
  category,
  series,
  domain,
  format = (v) => formatScore(v),
  labels = true,
  slots,
  labelWidth = 190,
}: Omit<BarProps, "height" | "hideValueAxis" | "formatAxis"> & { labelWidth?: number }) {
  const t = useChartTheme();
  // Phones: narrower label column (long names wrap) so the bars keep their room.
  const narrow = useNarrow();
  const labelW = narrow ? Math.min(labelWidth, 116) : labelWidth;
  const rowHeight = narrow ? 14 + series.length * 10 : 18 + series.length * 14;
  return (
    <ResponsiveContainer width="100%" height={40 + data.length * rowHeight + (series.length > 1 ? 30 : 0)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 52, left: 0, bottom: 4 }} barGap={2}>
        <CartesianGrid {...t.grid} horizontal={false} vertical />
        <XAxis type="number" {...t.axis} domain={domain ?? [0, "auto"]} tickFormatter={(v: number) => format(v)} />
        <YAxis
          type="category"
          dataKey={category}
          {...t.axis}
          width={labelW}
          interval={0}
          tick={{ ...t.axis.tick, fontSize: narrow ? 11 : 12 }}
        />
        <Tooltip {...t.tooltip} formatter={(v) => (typeof v === "number" ? format(v) : String(v))} />
        {series.length > 1 && <Legend verticalAlign="bottom" iconType="circle" itemSorter={() => 0} formatter={(v) => <span style={{ color: t.colours.text }}>{v}</span>} {...t.legend} />}
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            fill={t.series[(slots?.[i] ?? i) % t.series.length]}
            radius={[0, 4, 4, 0]}
            maxBarSize={narrow ? 12 : 22}
            isAnimationActive={t.animate}
          >
            {labels && (
              <LabelList
                dataKey={s.key}
                position="right"
                formatter={(v: unknown) => (typeof v === "number" ? format(v) : "")}
                style={{ fill: t.colours.muted, fontSize: 11 }}
              />
            )}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** One trust-score walk through time, with the per-employee alert threshold it
 * produces and the anomalous days shaded. */
export function TrustWalk({
  data,
  anomalous,
}: {
  data: { day: number; trust: number; threshold: number }[];
  anomalous: [number, number];
}) {
  const t = useChartTheme();
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 12, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid {...t.grid} />
        <ReferenceArea
          x1={anomalous[0]}
          x2={anomalous[1]}
          fill={t.colours.c3}
          fillOpacity={0.1}
          label={{ value: "anomalous days", position: "insideTop", fill: t.colours.muted, fontSize: 11 }}
        />
        <XAxis
          dataKey="day"
          {...t.axis}
          label={{ value: "Day", position: "insideBottomRight", offset: -2, fill: t.colours.muted, fontSize: 12 }}
        />
        <YAxis {...t.axis} domain={[0, 1]} width={40} />
        <Tooltip
          {...t.tooltip}
          cursor={{ stroke: t.colours.border }}
          labelFormatter={(d) => `Day ${d}`}
          formatter={(v) => (typeof v === "number" ? v.toFixed(3) : String(v))}
        />
        <Legend
          verticalAlign="bottom"
          iconType="plainline"
          formatter={(v) => <span style={{ color: t.colours.text }}>{v}</span>}
          {...t.legend}
        />
        <Line
          type="linear"
          dataKey="trust"
          name="Trust score"
          stroke={t.colours.c1}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
          isAnimationActive={t.animate}
        />
        <Line
          type="stepAfter"
          dataKey="threshold"
          name="Alert threshold"
          stroke={t.colours.c2}
          strokeWidth={2}
          strokeDasharray="6 4"
          dot={false}
          activeDot={{ r: 4 }}
          isAnimationActive={t.animate}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
