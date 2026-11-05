import { useMemo } from "react";
import { useTheme } from "./context";

/** Recharts props built from the CSS tokens in styles/tokens.css, so charts
 * follow the Tuks palette and the light/dark theme like the rest of the page.
 * Spread them onto the chart parts:
 *
 *   const t = useChartTheme();
 *   <CartesianGrid {...t.grid} /> <XAxis {...t.axis} /> <Tooltip {...t.tooltip} />
 */
export function useChartTheme() {
  const { resolved } = useTheme();

  return useMemo(() => {
    const css = getComputedStyle(document.documentElement);
    const v = (name: string) => css.getPropertyValue(name).trim();

    const colours = {
      text: v("--text"),
      muted: v("--text-muted"),
      border: v("--border"),
      surface: v("--surface"),
      accent: v("--accent"),
      accentSoft: v("--accent-soft"),
      good: v("--good"),
      bad: v("--bad"),
      gold: v("--up-gold"),
      red: v("--up-red"),
      c1: v("--chart-1"),
      c2: v("--chart-2"),
      c3: v("--chart-3"),
      c4: v("--chart-4"),
    };

    return {
      colours,
      /** Pass to every Bar / Line as isAnimationActive: off for reduced motion. */
      animate: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      /** Categorical series order: UP blue, gold, red, then green (the
       * --chart-* tokens, stepped separately for light and dark). */
      series: [colours.c1, colours.c2, colours.c3, colours.c4],
      grid: { strokeDasharray: "3 3", stroke: colours.border, vertical: false },
      axis: { stroke: colours.border, tick: { fill: colours.muted, fontSize: 12 } },
      tooltip: {
        contentStyle: {
          background: colours.surface,
          border: `1px solid ${colours.border}`,
          borderRadius: 8,
          color: colours.text,
        },
        labelStyle: { color: colours.text, fontWeight: 600 },
        itemStyle: { color: colours.text },
        cursor: { fill: colours.accentSoft },
      },
      legend: { wrapperStyle: { color: colours.muted, fontSize: 13 } },
    };
    // `resolved` is the dependency: the CSS values change when it does.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolved]);
}

export const formatScore = (value: unknown) =>
  typeof value === "number" ? value.toFixed(3) : String(value);
