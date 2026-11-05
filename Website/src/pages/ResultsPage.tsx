import { useEffect, useRef } from "react";
import { Link, Navigate, NavLink, useOutletContext, useParams } from "react-router-dom";
import { fetchPaperTable } from "../api";
import ResultTable from "../components/ResultTable";
import TableChart from "../components/TableChart";
import { ApiStatus, Badge, Loading } from "../components/ui";
import { useApi } from "../hooks/useApi";
import type { LayoutContext } from "../layout/Layout";
import { EXPERIMENT_TITLES, TAKEAWAYS, tableTitle } from "../tableInfo";

/** One results table: its chart, then the table itself. Significance tests
 * are folded away, since they back up the chart rather than tell the story. */
function TableBlock({ name }: { name: string }) {
  const { data, error, loading } = useApi(() => fetchPaperTable(name), [name]);
  const significance = name.startsWith("significance");

  if (error || loading) return <ApiStatus what="this table" loading={loading} error={error} />;
  if (!data?.available) return null;

  if (significance) {
    return (
      <details className="panel table-details">
        <summary>Significance tests: is each strategy separable from the best?</summary>
        <ResultTable table={data} />
      </details>
    );
  }
  return (
    <section className="panel">
      <h2>{tableTitle(name)}</h2>
      <div className="chart-panel">
        <TableChart table={data} />
      </div>
      <ResultTable table={data} />
    </section>
  );
}

/** Alert lists exist for the two synthetic datasets' strategy comparisons. */
const ALERTS: Record<string, { to: string; label: string }> = {
  E1: { to: "/alerts/month", label: "Ranked alerts on the 30-day logs" },
  E2: { to: "/alerts/single_day", label: "Ranked alerts on the single-day logs" },
};

/** All results on one page: E1–E10 as tabs, one experiment shown at a time. */
export default function ResultsPage() {
  const { id } = useParams();
  const { experiments: all } = useOutletContext<LayoutContext>();
  const experiments = all.filter((e) => e.id.startsWith("E"));
  const tabs = useRef<HTMLElement>(null);

  // On narrow screens the tab row scrolls: keep the selected tab in view.
  useEffect(() => {
    tabs.current?.querySelector(".exp-tab.active")?.scrollIntoView({ block: "nearest", inline: "center" });
  }, [id, experiments.length]);

  if (experiments.length === 0) return <Loading />;
  const index = experiments.findIndex((e) => e.id === id);
  if (index < 0) return <Navigate to={`/results/${experiments[0].id}`} replace />;

  const experiment = experiments[index];
  const prev = experiments[index - 1];
  const next = experiments[index + 1];

  return (
    <>
      <header className="results-header">
        <h1>Results</h1>
        <nav className="exp-tabs" aria-label="Experiments" ref={tabs}>
          {experiments.map((e) => (
            <NavLink
              key={e.id}
              to={`/results/${e.id}`}
              className={({ isActive }) => (isActive ? "exp-tab active" : "exp-tab")}
              title={EXPERIMENT_TITLES[e.id]}
            >
              {e.id}
            </NavLink>
          ))}
        </nav>
      </header>

      <section className="exp-intro">
        <div className="exp-intro-top">
          <Badge>{experiment.id}</Badge>
          <span className="muted">Dataset: {experiment.dataset}</span>
        </div>
        <h2>{EXPERIMENT_TITLES[experiment.id]}</h2>
        <p className="lead">{experiment.question}</p>
        {TAKEAWAYS[experiment.id] && (
          <p className="reading">
            <strong>Summary.</strong> {TAKEAWAYS[experiment.id]}
          </p>
        )}
      </section>

      {experiment.tables.map((t) => (
        <TableBlock key={t} name={t} />
      ))}

      {ALERTS[experiment.id] && (
        <div className="link-buttons">
          <Link to={ALERTS[experiment.id].to} className="button-link">
            {ALERTS[experiment.id].label}
          </Link>
        </div>
      )}

      <nav className="prev-next" aria-label="Previous and next experiment">
        {prev ? <Link to={`/results/${prev.id}`}>← {prev.id} {EXPERIMENT_TITLES[prev.id]}</Link> : <span />}
        {next ? <Link to={`/results/${next.id}`}>{next.id} {EXPERIMENT_TITLES[next.id]} →</Link> : <span />}
      </nav>
    </>
  );
}

/** Old links (/experiment/E4, /table/results_month) land on the matching tab. */
export function LegacyResultsRedirect() {
  const { id, name } = useParams();
  const { experiments } = useOutletContext<LayoutContext>();
  if (id) return <Navigate to={`/results/${id}`} replace />;
  if (experiments.length === 0) return <Loading />;
  const owner = experiments.find((e) => e.tables.includes(name ?? ""));
  return <Navigate to={owner ? `/results/${owner.id}` : "/results"} replace />;
}
