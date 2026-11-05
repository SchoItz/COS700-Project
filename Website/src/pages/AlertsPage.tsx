import { Link, useParams } from "react-router-dom";
import { fetchAlerts } from "../api";
import { ApiStatus, Badge, PageHeader } from "../components/ui";
import { useApi } from "../hooks/useApi";
import NotFound from "./NotFound";

const TITLES: Record<string, string> = { month: "30-day logs", single_day: "Single-day logs" };

export default function AlertsPage() {
  const { dataset = "" } = useParams();
  const { data, error, loading, notFound } = useApi(() => fetchAlerts(dataset), [dataset]);

  if (!(dataset in TITLES) || notFound) return <NotFound />;

  return (
    <>
      <PageHeader
        crumbs={
          <>
            <Link to="/results">Results</Link> / Alerts
          </>
        }
        title={`Ranked alerts: ${TITLES[dataset]}`}
        lead="What the decision layer hands an analyst: employee-days scored by the best strategy, each scored by a model that never trained on it, and raised when the score passes that employee's own trust-derived threshold. Highest score first."
      />
      <div>
        <div className="dataset-toggle">
          {Object.entries(TITLES).map(([key, label]) => (
            <Link key={key} to={`/alerts/${key}`} className={key === dataset ? "toggle active" : "toggle"}>
              {label}
            </Link>
          ))}
        </div>
      </div>
      <ApiStatus what="the alerts" loading={loading} error={error} />
      {data && (
        <div className="panel">
          <p>
            {data.total.toLocaleString()} alerts raised, {data.malicious.toLocaleString()} of them
            genuinely malicious. Showing the first {data.rows.length}.
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>When</th>
                  <th>Score</th>
                  <th>Threshold</th>
                  <th>Trust</th>
                  <th>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.user_id}</td>
                    <td>{r.timestamp.slice(0, 16)}</td>
                    <td>{r.score.toFixed(3)}</td>
                    <td>{r.threshold.toFixed(3)}</td>
                    <td>{r.trust_score.toFixed(3)}</td>
                    <td>
                      {r.label ? <Badge tone="green">Malicious</Badge> : <Badge tone="red">False alarm</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
