import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  fetchModel,
  fetchModels,
  type Metrics,
  type ModelDetail,
  type RankedResult,
  type VariantResult,
} from "../api";
import { ApiStatus, Badge, PageHeader, ParadigmBadge, PrevNext } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { formatScore, useChartTheme } from "../theme/chart";
import NotFound from "./NotFound";

const f3 = (v: number | null | undefined) => (v == null ? "–" : v.toFixed(3));
const f4 = (v: number | null | undefined) => (v == null ? "–" : v.toFixed(4));
const f1d = (v: number | null | undefined) => (v == null ? "–" : v.toFixed(1));

const VARIANT_LABELS: Record<string, string> = {
  single_day_snapshot: "Single-day snapshot",
  multi_day_temporal: "Multi-day temporal",
  no_trust: "No trust",
  trust_as_feature: "Trust as feature",
  trust_as_sensitivity: "Trust as sensitivity",
  none: "Class weighting only",
  smote: "SMOTE",
  undersample: "Under-sampling",
};

function MetricCells({ m, fpDigits = 1 }: { m: Metrics; fpDigits?: number }) {
  return (
    <>
      <td>{f3(m.f1)}</td>
      <td>{f3(m.precision)}</td>
      <td>{f3(m.recall)}</td>
      <td>{f4(m.false_positive_rate)}</td>
      <td>{f3(m.pr_auc)}</td>
      <td>{fpDigits === 0 ? (m.false_positive_count ?? "–") : f1d(m.false_positive_count)}</td>
    </>
  );
}

const METRIC_HEAD = ["F1", "P", "R", "FPR", "PR-AUC", "FP"];

function Head({ first }: { first: string[] }) {
  return (
    <thead>
      <tr>
        {first.map((h) => (
          <th key={h}>{h}</th>
        ))}
        {METRIC_HEAD.map((h) => (
          <th key={h}>{h}</th>
        ))}
      </tr>
    </thead>
  );
}

function significanceText(r: RankedResult) {
  const s = r.significance;
  if (!s) return "–";
  if (s.is_best) return "Best strategy";
  return `${s.significant ? "Significantly worse" : "Not separated"} (p = ${f4(s.p_value)})`;
}

function VariantTable({ rows, label }: { rows: VariantResult[]; label: string }) {
  return (
    <div className="table-scroll">
      <table>
        <Head first={[label]} />
        <tbody>
          {rows.map((r) => (
            <tr key={r.variant}>
              <td>{VARIANT_LABELS[r.variant] ?? r.variant}</td>
              <MetricCells m={r} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ModelPage() {
  const { name = "" } = useParams();
  const { data: model, error, loading, notFound } = useApi<ModelDetail>(() => fetchModel(name), [name]);
  const all = useApi(fetchModels, []).data ?? [];
  const ct = useChartTheme();

  if (notFound) return <NotFound />;
  if (!model) return <ApiStatus what="this model" loading={loading} error={error} />;

  const index = all.findIndex((m) => m.name === name);
  const prev = all[index - 1];
  const next = all[index + 1];

  const chart = [
    ...model.cross_validation.map((r) => ({ setting: `${r.experiment} cross-val.`, f1: r.f1 })),
    ...model.generalisation.map((r) => ({ setting: `${r.experiment} transfer`, f1: r.f1 })),
  ];

  return (
    <>
      <PageHeader
        crumbs={
          <>
            <Link to="/models">Models</Link> / {model.title}
          </>
        }
        title={model.title}
      >
        <p className="card-top">
          <Badge>{model.family === "individual" ? "Individual" : "Combined"}</Badge>
          <ParadigmBadge paradigm={model.paradigm} />
        </p>
        <p className="lead">{model.summary}</p>
      </PageHeader>

      <div className="panel">
        <h2>How it is built</h2>
        <ul className="detail-list">
          {model.details.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>
        <p className="muted">
          <strong>Class imbalance:</strong> {model.imbalance}
        </p>
      </div>

      {chart.length > 0 && (
        <div className="panel">
          <h2>F1 across datasets</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chart} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid {...ct.grid} />
              <XAxis dataKey="setting" {...ct.axis} />
              <YAxis {...ct.axis} domain={[0, 1]} />
              <Tooltip
            {...ct.tooltip}
            formatter={formatScore}
              />
              <Bar dataKey="f1" name="F1" fill={ct.colours.accent} isAnimationActive={ct.animate} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {model.cross_validation.length > 0 && (
        <div className="panel">
          <h2>Cross-validated results</h2>
          <p className="muted">
            Means over ten stratified folds; FP is the mean false-positive count per fold. Rank is
            by F1 among the fifteen strategies.
          </p>
          <div className="table-scroll">
            <table>
              <Head first={["Exp.", "Dataset"]} />
              <tbody>
                {model.cross_validation.map((r) => (
                  <tr key={r.experiment}>
                    <td>
                      <Link to={`/results/${r.experiment}`}>{r.experiment}</Link>
                    </td>
                    <td>{r.dataset}</td>
                    <MetricCells m={r} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Exp.</th>
                  <th>Rank by F1</th>
                  <th>Against the best strategy (Wilcoxon, Holm-Bonferroni)</th>
                </tr>
              </thead>
              <tbody>
                {model.cross_validation.map((r) => (
                  <tr key={r.experiment}>
                    <td>{r.experiment}</td>
                    <td>
                      {r.rank} of {r.of}
                    </td>
                    <td>{significanceText(r)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {model.generalisation.length > 0 && (
        <div className="panel">
          <h2>Generalisation to an unseen dataset</h2>
          <p className="muted">
            Trained once, then tested on the full Kaggle dataset. FP is the absolute false-positive
            count over the whole test set.
          </p>
          <div className="table-scroll">
            <table>
              <Head first={["Exp.", "Setting", "Rank"]} />
              <tbody>
                {model.generalisation.map((r) => (
                  <tr key={r.experiment}>
                    <td>
                      <Link to={`/results/${r.experiment}`}>{r.experiment}</Link>
                    </td>
                    <td>{r.dataset}</td>
                    <td>
                      {r.rank} of {r.of}
                    </td>
                    <MetricCells m={r} fpDigits={0} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {model.ablation.map((a) => (
        <div className="panel" key={a.experiment}>
          <h2>
            Temporal ablation: {a.dataset} ({a.experiment})
          </h2>
          <VariantTable rows={a.arms} label="Features" />
        </div>
      ))}
      {model.ablation.length === 0 && (
        <p className="muted">
          This model is not part of the temporal ablation (E4, E5), which runs the nine
          scikit-learn strategies only.
        </p>
      )}

      {model.trust.length > 0 && (
        <div className="panel">
          <h2>Trust integration (E8)</h2>
          <VariantTable rows={model.trust} label="Design" />
        </div>
      )}

      {model.resampling.length > 0 && (
        <div className="panel">
          <h2>Class-imbalance treatment (E9)</h2>
          <VariantTable rows={model.resampling} label="Treatment" />
        </div>
      )}

      <PrevNext
        prev={prev && { to: `/model/${prev.name}`, label: prev.title }}
        next={next && { to: `/model/${next.name}`, label: next.title }}
      />
    </>
  );
}
