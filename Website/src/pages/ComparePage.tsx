import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchCompare, fetchModels } from "../api";
import { ApiStatus, PageHeader } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { useNarrow } from "../hooks/useNarrow";
import { useChartTheme } from "../theme/chart";

/** Pick a metric and a setting; every model is ranked on one chart. The grid
 * below shows all settings at once, for reading a model across them. */

const LOWER_IS_BETTER = new Set(["false_positive_rate"]);

const SETTING_NOTES: Record<string, string> = {
  E1: "Cross-validated on the 30-day logs.",
  E2: "Cross-validated on the single-day logs.",
  E3: "Cross-validated on the third-party synthetic Kaggle data.",
  E6: "Trained on the 30-day logs, tested on the full Kaggle dataset it never saw.",
  E7: "Trained on the single-day logs, tested on the full Kaggle dataset it never saw.",
};

/** Heatmap colour: stronger accent is better. The false-positive rate is
 * inverted and saturates at 0.3. */
function shade(metric: string, v: number | null): string | undefined {
  if (v == null) return undefined;
  const strength = LOWER_IS_BETTER.has(metric) ? 1 - Math.min(v / 0.3, 1) : Math.min(Math.max(v, 0), 1);
  return `color-mix(in srgb, var(--accent) ${Math.round(6 + strength * 46)}%, transparent)`;
}

export default function ComparePage() {
  const [metric, setMetric] = useState("f1");
  const [setting, setSetting] = useState("E1");
  const { data, error, loading } = useApi(() => fetchCompare(metric), [metric]);
  const titles = Object.fromEntries((useApi(fetchModels, []).data ?? []).map((m) => [m.name, m.title]));
  const t = useChartTheme();
  const navigate = useNavigate();
  const narrow = useNarrow();

  const lower = LOWER_IS_BETTER.has(metric);
  const digits = lower ? 4 : 3;
  const fmt = (v: number) => v.toFixed(digits);
  const title = (name: string) => titles[name] ?? name.replace(/_/g, " ");
  const metricLabel = data?.metrics[metric] ?? "F1";
  const settingLabel = data?.columns.find((c) => c.id === setting)?.label ?? setting;

  // Models ranked best-first on the chosen setting.
  const ranked = useMemo(() => {
    if (!data) return [];
    return data.models
      .filter((m) => m.scores[setting] != null)
      .map((m) => ({ name: m.name, label: title(m.name), family: m.family, value: m.scores[setting] as number }))
      .sort((a, b) => (lower ? a.value - b.value : b.value - a.value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, setting, lower, titles]);

  const best = ranked[0];
  const familyMean = (family: string) => {
    const v = ranked.filter((r) => r.family === family).map((r) => r.value);
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
  };
  const indMean = familyMean("individual");
  const combMean = familyMean("combined");

  // Grid: rows in the same order as the chart.
  const order = Object.fromEntries(ranked.map((r, i) => [r.name, i]));
  const gridRows = data ? [...data.models].sort((a, b) => (order[a.name] ?? 99) - (order[b.name] ?? 99)) : [];
  const bestPerColumn: Record<string, number> = {};
  for (const c of data?.columns ?? []) {
    const v = (data?.models ?? []).map((m) => m.scores[c.id]).filter((x): x is number => x != null);
    if (v.length) bestPerColumn[c.id] = lower ? Math.min(...v) : Math.max(...v);
  }

  const familyColour = (family: string) => (family === "individual" ? t.colours.c1 : t.colours.c2);

  return (
    <>
      <PageHeader
        title="Compare models"
        lead="Choose a score and a setting to rank all fifteen strategies. Blue bars are individual models, gold bars are combined ones."
      />

      <div className="panel compare-controls">
        <div>
          <span className="control-label">Score</span>
          <div className="dataset-toggle">
            {Object.entries(data?.metrics ?? { f1: "F1" }).map(([k, label]) => (
              <button key={k} className={k === metric ? "toggle active" : "toggle"} onClick={() => setMetric(k)}>
                {label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <span className="control-label">Setting</span>
          <div className="dataset-toggle">
            {(data?.columns ?? []).map((c) => (
              <button key={c.id} className={c.id === setting ? "toggle active" : "toggle"} onClick={() => setSetting(c.id)}>
                {c.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <ApiStatus what="the comparison" loading={loading} error={error} />

      {data && best && (
        <section className="panel">
          <h2>
            {metricLabel}, {settingLabel}
          </h2>
          <p className="muted compare-note">
            {SETTING_NOTES[setting]} {lower ? "Lower is better." : "Higher is better."}{" "}
            <Link to="/glossary">What does {metricLabel} mean?</Link>
          </p>

          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-value">{fmt(best.value)}</div>
              <div className="stat-label">
                Best: <Link to={`/model/${best.name}`}>{best.label}</Link>
              </div>
            </div>
            {indMean != null && (
              <div className="stat-card">
                <div className="stat-value">{fmt(indMean)}</div>
                <div className="stat-label">Average individual model</div>
              </div>
            )}
            {combMean != null && (
              <div className="stat-card">
                <div className="stat-value">{fmt(combMean)}</div>
                <div className="stat-label">Average combined model</div>
              </div>
            )}
          </div>

          <div className="compare-legend" aria-hidden>
            <span>
              <i style={{ background: t.colours.c1 }} /> Individual
            </span>
            <span>
              <i style={{ background: t.colours.c2 }} /> Combined
            </span>
          </div>
          <ResponsiveContainer width="100%" height={40 + ranked.length * 30}>
            <BarChart data={ranked} layout="vertical" margin={{ top: 4, right: 56, left: 0, bottom: 4 }}>
              <CartesianGrid {...t.grid} horizontal={false} vertical />
              <XAxis
                type="number"
                {...t.axis}
                domain={lower ? [0, "auto"] : [0, 1]}
                ticks={lower ? undefined : [0, 0.2, 0.4, 0.6, 0.8, 1]}
                tickFormatter={(v: number) => (lower ? v.toFixed(2) : v.toFixed(1))}
              />
              <YAxis type="category" dataKey="label" {...t.axis} width={narrow ? 116 : 170} interval={0} />
              <Tooltip
                {...t.tooltip}
                formatter={(v) => [typeof v === "number" ? fmt(v) : String(v), metricLabel]}
              />
              <Bar
                dataKey="value"
                radius={[0, 4, 4, 0]}
                maxBarSize={20}
                isAnimationActive={t.animate}
                cursor="pointer"
                onClick={(d) => {
                  const name = (d as { payload?: { name?: string } }).payload?.name;
                  if (name) navigate(`/model/${name}`);
                }}
              >
                {ranked.map((r) => (
                  <Cell key={r.name} fill={familyColour(r.family)} />
                ))}
                <LabelList
                  dataKey="value"
                  position="right"
                  formatter={(v: unknown) => (typeof v === "number" ? fmt(v) : "")}
                  style={{ fill: t.colours.muted, fontSize: 11 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="table-note">Click a bar to open that model.</p>
        </section>
      )}

      {data && (
        <section className="panel">
          <h2>Every setting at once</h2>
          <p className="muted compare-note">
            Read across a row to see whether a model holds up on unseen data (the last two
            columns). Darker cells are better; the outlined cell is the best in its column.
          </p>
          <div className="table-scroll">
            <table className="heatmap">
              <thead>
                <tr>
                  <th>Model</th>
                  {data.columns.map((c) => (
                    <th key={c.id} className={c.id === setting ? "selected-col" : undefined}>
                      <button className="sort" onClick={() => setSetting(c.id)} title="Rank by this setting">
                        {c.label}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {gridRows.map((m) => (
                  <tr key={m.name}>
                    <td>
                      <span
                        className="family-dot"
                        style={{ background: familyColour(m.family) }}
                        title={m.family === "individual" ? "Individual" : "Combined"}
                      />
                      <Link to={`/model/${m.name}`}>{title(m.name)}</Link>
                    </td>
                    {data.columns.map((c) => {
                      const v = m.scores[c.id];
                      return (
                        <td
                          key={c.id}
                          style={{ background: shade(metric, v) }}
                          className={v != null && v === bestPerColumn[c.id] ? "best-cell" : undefined}
                        >
                          {v == null ? "–" : v.toFixed(digits)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}
