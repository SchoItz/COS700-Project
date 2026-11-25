import { Link } from "react-router-dom";
import { fetchFindings } from "../api";
import { GroupedBars, HorizontalBars } from "../components/Charts";
import { ApiStatus, PageHeader, Stat } from "../components/ui";
import { useApi } from "../hooks/useApi";

const f3 = (v: number) => v.toFixed(3);
const signed = (v: number) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(3)}`;
const pct = (v: number) => `${(v * 100).toFixed(1)}%`;
const name = (s: string) => s.replace(/_/g, " ");
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function ChartBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <figure className="chart-box">
      <figcaption>{title}</figcaption>
      {children}
    </figure>
  );
}

const TRUST_ARMS = [
  ["no_trust", "No trust"],
  ["trust_as_feature", "Trust as feature"],
  ["trust_as_sensitivity", "Trust as threshold"],
] as const;

const IMBALANCE_LABELS: Record<string, string> = {
  none: "Class weighting only",
  smote: "+ SMOTE",
  undersample: "+ Under-sampling",
};

function Reading({ children }: { children: React.ReactNode }) {
  return (
    <p className="reading">{children}</p>
  );
}

export default function FindingsPage() {
  const { data, error, loading } = useApi(fetchFindings, []);

  const abl = data?.sq1.ablation;
  const sq2 = data?.sq2;
  const sq3 = data?.sq3;

  return (
    <>
      <PageHeader title="Findings" eyebrow="Research question">
        <p className="lead">
          How can a framework that combines behavioural signals analysed over time, trust
          modelling, and comparison of different strategies improve insider threat detection?
        </p>
        <p className="muted">
          Each sub-question below shows the current numbers, computed from the result files,
          followed by how the paper reads them and where to see the evidence.
        </p>
      </PageHeader>
      <ApiStatus what="the findings" loading={loading} error={error} />

      <section className="panel">
        <h2>SQ1. Which signals distinguish malicious from benign activity?</h2>
        {data && abl && (
          <>
            <div className="stat-grid">
              {Object.entries(abl).map(([key, a]) => (
                <Stat
                  key={key}
                  value={signed(a.gain)}
                  label={`Mean F1 gained from multi-day history, ${key === "month" ? "30-day logs" : "Kaggle"} (${f3(a.snapshot_f1)} → ${f3(a.temporal_f1)})`}
                />
              ))}
              {data.sq1.top_signal && (
                <Stat
                  value={f3(data.sq1.top_signal.importance)}
                  label={`Top signal on the 30-day logs: ${name(data.sq1.top_signal.feature.replace(/^\w+__/, ""))}`}
                />
              )}
            </div>
            <div className="grid-2 charts">
              <ChartBox title="Mean F1: single-day snapshot vs multi-day history">
                <GroupedBars
                  data={Object.entries(abl).map(([key, a]) => ({
                    name: key === "month" ? "30-day logs" : "Kaggle",
                    snapshot: a.snapshot_f1,
                    history: a.temporal_f1,
                  }))}
                  category="name"
                  series={[
                    { key: "snapshot", label: "Single-day snapshot" },
                    { key: "history", label: "Multi-day history" },
                  ]}
                  domain={[0, 1]}
                />
              </ChartBox>
              <ChartBox title="Share of importance by kind of signal (30-day logs)">
                <HorizontalBars
                  data={Object.entries(data.sq1.signal_shares).map(([kind, share]) => ({
                    kind: cap(kind),
                    share,
                  }))}
                  category="kind"
                  series={[{ key: "share", label: "Share of importance" }]}
                  domain={[0, 1]}
                  format={pct}
                  labelWidth={170}
                />
              </ChartBox>
            </div>
            <details className="table-details">
              <summary>Show as a table</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Kind of signal</th>
                    <th>Share of importance (30-day logs)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.sq1.signal_shares).map(([kind, share]) => (
                    <tr key={kind}>
                      <td>{kind}</td>
                      <td>{pct(share)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </details>
          </>
        )}
        <Reading>
          The answer depends on the dataset. Where anomalies are extreme in absolute terms, raw
          values already separate the classes and history adds little; on the Kaggle data, what marks a
          malicious day is being extreme <em>for that employee</em>, which only a per-employee
          baseline can express.
        </Reading>
        <p>
          Evidence: <Link to="/results/E4">E4</Link> · <Link to="/results/E5">E5</Link> ·{" "}
          <Link to="/results/E10">E10</Link>
        </p>
      </section>

      <section className="panel">
        <h2>SQ2. Can a trust score reduce false positives?</h2>
        {sq2 && (
          <>
            <div className="stat-grid">
              <Stat value={pct(sq2.fp_reduction)} label="Fewer false positives with trust as a per-employee threshold" />
              <Stat
                value={`${f3(sq2.arms.trust_as_feature.precision)} → ${f3(sq2.arms.trust_as_sensitivity.precision)}`}
                label="Mean precision, trust as feature → as threshold"
              />
              <Stat
                value={`${f3(sq2.arms.trust_as_feature.recall)} → ${f3(sq2.arms.trust_as_sensitivity.recall)}`}
                label="Mean recall, the cost"
              />
              <Stat
                value={`${f3(sq2.arms.no_trust.f1)} / ${f3(sq2.arms.trust_as_feature.f1)}`}
                label="Mean F1 with no trust / trust as feature"
              />
            </div>
            <div className="grid-2 charts">
              <ChartBox title="Mean false positives per fold">
                <GroupedBars
                  data={TRUST_ARMS.map(([key, label]) => ({
                    name: label,
                    fp: sq2.arms[key].false_positive_count,
                  }))}
                  category="name"
                  series={[{ key: "fp", label: "False positives per fold" }]}
                />
              </ChartBox>
              <ChartBox title="Precision, recall and F1 for each design">
                <GroupedBars
                  data={TRUST_ARMS.map(([key, label]) => ({
                    name: label,
                    precision: sq2.arms[key].precision,
                    recall: sq2.arms[key].recall,
                    f1: sq2.arms[key].f1,
                  }))}
                  category="name"
                  series={[
                    { key: "precision", label: "Precision" },
                    { key: "recall", label: "Recall" },
                    { key: "f1", label: "F1" },
                  ]}
                  domain={[0, 1]}
                />
              </ChartBox>
            </div>
          </>
        )}
        <Reading>
          Trust as a model input changes nothing measurable, because it is a function of the
          deviation features the model already has. As a per-employee threshold it suppresses false
          positives, at a cost in recall; unchanged average precision shows it moves the decision
          boundary rather than improving the ranking.
        </Reading>
        <p>
          Evidence: <Link to="/results/E8">E8</Link>
        </p>
      </section>

      <section className="panel">
        <h2>SQ3. Individual, combined or hybrid?</h2>
        {sq3 && (
          <>
            <div className="grid-2 charts">
              <ChartBox title="Best individual vs best combined strategy (F1)">
                <GroupedBars
                  data={[...Object.values(sq3.comparison), ...Object.values(sq3.transfer)].map((c) => ({
                    name: c.label.replace(" → ", "→"),
                    individual: c.best_individual,
                    combined: c.best_combined,
                  }))}
                  category="name"
                  series={[
                    { key: "individual", label: "Best individual" },
                    { key: "combined", label: "Best combined" },
                  ]}
                  domain={[0, 1]}
                  labels={false}
                  height={280}
                />
              </ChartBox>
              <ChartBox title="Average strategy in each family (F1)">
                <GroupedBars
                  data={[...Object.values(sq3.comparison), ...Object.values(sq3.transfer)].map((c) => ({
                    name: c.label.replace(" → ", "→"),
                    individual: c.individual_mean,
                    combined: c.combined_mean,
                  }))}
                  category="name"
                  series={[
                    { key: "individual", label: "Individual, mean" },
                    { key: "combined", label: "Combined, mean" },
                  ]}
                  domain={[0, 1]}
                  labels={false}
                  height={280}
                />
              </ChartBox>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Setting</th>
                    <th>Best strategy</th>
                    <th>Best F1</th>
                    <th>Best individual</th>
                    <th>Best combined</th>
                    <th>Individual mean</th>
                    <th>Combined mean</th>
                  </tr>
                </thead>
                <tbody>
                  {[...Object.values(sq3.comparison), ...Object.values(sq3.transfer)].map((c) => (
                    <tr key={c.label}>
                      <td>{c.label}</td>
                      <td>
                        <Link to={`/model/${c.best}`}>{name(c.best)}</Link>{" "}
                        <span className="muted">({c.best_family})</span>
                      </td>
                      <td>{f3(c.best_f1)}</td>
                      <td>{f3(c.best_individual)}</td>
                      <td>{f3(c.best_combined)}</td>
                      <td>{f3(c.individual_mean)}</td>
                      <td>{f3(c.combined_mean)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="table-note">
              The first three rows are cross-validated within a dataset; the last two are trained on
              one dataset and tested on the full Kaggle dataset.
            </p>
          </>
        )}
        <Reading>
          The claim that hybrids dominate splits in two. The best single strategy is not beaten by
          a combined one under cross-validation, but combined strategies have the better average
          because they avoid the worst failures: combining models is insurance against choosing
          badly. On transfer to an unseen dataset the ranking changes almost completely.
        </Reading>
        <p>
          Evidence: <Link to="/results/E1">E1</Link> · <Link to="/results/E2">E2</Link> ·{" "}
          <Link to="/results/E3">E3</Link> · <Link to="/results/E6">E6</Link> ·{" "}
          <Link to="/results/E7">E7</Link> · <Link to="/compare">Compare all models</Link>
        </p>
      </section>

      {data?.imbalance && (
        <section className="panel">
          <h2>Class imbalance</h2>
          <div className="stat-grid">
            {Object.entries(data.imbalance).map(([k, v]) => (
              <Stat
                key={k}
                value={f3(v.f1)}
                label={`Mean F1, ${k === "none" ? "class weighting only" : k === "smote" ? "SMOTE" : "under-sampling"}`}
              />
            ))}
          </div>
          <ChartBox title="Mean precision, recall and F1 for each treatment (30-day logs)">
            <GroupedBars
              data={Object.entries(data.imbalance).map(([k, v]) => ({
                name: IMBALANCE_LABELS[k] ?? k,
                precision: v.precision,
                recall: v.recall,
                f1: v.f1,
              }))}
              category="name"
              series={[
                { key: "precision", label: "Precision" },
                { key: "recall", label: "Recall" },
                { key: "f1", label: "F1" },
              ]}
              domain={[0, 1]}
            />
          </ChartBox>
          <p>
            SMOTE lifts the average without costing precision; under-sampling buys recall by
            throwing away benign rows, and precision drops.
          </p>
          <p>
            Evidence: <Link to="/results/E9">E9</Link>
          </p>
        </section>
      )}
    </>
  );
}
