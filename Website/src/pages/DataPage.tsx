import { Link } from "react-router-dom";
import {
  fetchKaggleDetails,
  fetchMonthDetails,
  fetchPaperTable,
} from "../api";
import { GroupedBars } from "../components/Charts";
import ResultTable from "../components/ResultTable";
import { ApiStatus, PageHeader, Stat } from "../components/ui";
import { useApi } from "../hooks/useApi";

const ARCHETYPES: Record<string, string> = {
  gradual_escalation: "Gradual escalation over two weeks",
  sudden_spike: "A sudden three-day burst that fully reverts",
  off_hours_only: "Off-hours shift: volumes stay at baseline, only login time moves",
  weekend_infiltrator: "Weekend activity while weekdays stay normal",
  subtle_exfiltration: "Mild sustained increase in data transfer only",
};

export default function DataPage() {
  const { data: table, error, loading } = useApi(() => fetchPaperTable("datasets"), []);
  const month = useApi(fetchMonthDetails, []).data;
  const kaggle = useApi(fetchKaggleDetails, []).data;

  return (
    <>
      <PageHeader
        title="Data"
        lead="Three datasets of differing difficulty and origin: all synthetic, two from my own generators and one from a third party. All are mapped onto the framework's common schema before anything else happens."
      />
      <ApiStatus what="the datasets" loading={loading} error={error} />
      {table?.available && (
        <div className="panel">
          <div className="stat-grid">
            {table.sections[0].rows.map((r) => (
              <Stat
                key={r.key}
                value={(r.values.rows ?? 0).toLocaleString()}
                label={`${r.label.text}: employee-days from ${(r.values.employees ?? 0).toLocaleString()} employees`}
              />
            ))}
          </div>
          <div className="charts">
            <figure className="chart-box">
              <figcaption>Malicious share of rows: every dataset is heavily imbalanced</figcaption>
              <GroupedBars
                data={table.sections[0].rows.map((r) => ({
                  name: r.label.text.replace(" insider threat", ""),
                  rate: r.values.positive_rate,
                }))}
                category="name"
                series={[{ key: "rate", label: "Malicious share" }]}
                format={(v) => `${(v * 100).toFixed(1)}%`}
                formatAxis
                slots={[2]}
              />
            </figure>
          </div>
          <ResultTable table={table} />
        </div>
      )}

      <section className="panel">
        <h2>30-day logs (synthetic)</h2>
        <p>
          Employees observed over consecutive days, with insider threats split across five
          behavioural archetypes. Normal values carry seeded jitter, and some ordinary employees are
          deliberately noisier than their peers, so a strategy that treats any deviation as a threat
          is penalised.
        </p>
        {month && (
          <>
            <p className="muted">
              {month.n_employees} employees over {month.n_days} days; {month.n_insider_threats}{" "}
              insider threats.
            </p>
            <ul className="detail-list">
              {Object.entries(month.archetypes).map(([type, ids]) => (
                <li key={type}>
                  <strong>{ARCHETYPES[type] ?? type}</strong>
                  <span className="muted"> — {ids.length} employees</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="panel">
        <h2>Single-day logs (synthetic)</h2>
        <p>
          A weekday corpus of employees observed over a thousand weeks, one row per employee-day.
          Some employees drift into anomalous behaviour partway through. The report uses a
          contiguous 20-week window per employee, straddling their own drift onset, with benign
          window starts drawn from the same onsets so that calendar time cannot predict the label.
        </p>
        <div className="link-buttons">
          <Link to="/data/corpus" className="button-link">Explore the full weekday corpus</Link>
        </div>
      </section>

      <section className="panel">
        <h2>Kaggle insider-threat dataset (synthetic, third party)</h2>
        <p>
          Daily records for employees in a classified environment, covering physical access,
          printing, optical-media burning and travel. It is mapped onto the schema by behavioural
          analogue (for example burn requests become device activity); email and failed-login
          counters have no counterpart and are zero. The per-day malicious flag is the label.
          Within-dataset experiments sample whole employees; the generalisation experiments use
          the full dataset.
        </p>
        {kaggle && (
          <p className="muted">
            {kaggle.n_employees.toLocaleString()} employees, {kaggle.total_records.toLocaleString()}{" "}
            records, {kaggle.n_malicious_days.toLocaleString()} malicious days, from{" "}
            {kaggle.date_range.start} to {kaggle.date_range.end}.
          </p>
        )}
      </section>
    </>
  );
}
