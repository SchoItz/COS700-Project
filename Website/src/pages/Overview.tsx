import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { fetchFindings, fetchPaperTable, type PaperTable, type Row } from "../api";
import { GroupedBars } from "../components/Charts";
import { ApiStatus } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { useTheme } from "../theme/context";

/** The opening page is the A1 poster as a web page: the same banner, the same
 * four columns (Introduction and Methodology, Results: Time and trust,
 * Results: Model choice, Conclusions), the same wording and the same chart
 * colours, which follow the site's light and dark themes.
 * Chart values are read from the exported result files; the text matches the
 * poster (Poster/build_poster.py), which is built from the same results.
 * The poster's QR box is replaced by a Contact box on the web, and each box
 * ends with buttons into the matching pages of the site. */

const CONTACT_EMAIL = "u19024232@tuks.co.za";
const CONTACT_PHONE = "076 272 1484";

/** Bar colours: the poster's (Poster/build_poster.py) in light mode, and
 * brighter equivalents in dark mode so the bars stand out on the dark boxes. */
const BARS = {
  light: { strong: "#003366", mid: "#005eb8", soft: "#9db3cf" },
  dark: { strong: "#6aaef2", mid: "#2f78c8", soft: "#5d7190" },
};

const f3 = (v: number) => v.toFixed(3);

function rows(table: PaperTable | null): Row[] {
  return table?.available ? table.sections.flatMap((s) => s.rows) : [];
}

const LAYERS = [
  { id: "data", title: "Data", text: "One common 17-column schema for every source" },
  { id: "temporal", title: "Temporal", text: "14-event rolling baseline with self and peer z-scores" },
  { id: "trust", title: "Trust", text: "Score erodes with persistent deviation, recovers slowly" },
  { id: "detection", title: "Detection", text: "15 strategies: 9 individual, 6 combined" },
  { id: "validation", title: "Validation", text: "10 shared folds, Wilcoxon with Holm-Bonferroni" },
];

interface Action {
  to: string;
  label: string;
}

/** A poster box; `actions` become buttons under its content. */
function Box({ title, actions, children }: { title: string; actions?: Action[]; children: ReactNode }) {
  return (
    <section className="poster-box">
      <h2 className="poster-head">{title}</h2>
      <div className="poster-body">
        <div className="poster-content">{children}</div>
        {actions && (
          <div className="poster-actions">
            {actions.map((a) => (
              <Link key={a.to} to={a.to} className="poster-button">
                {a.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function SQ({ n }: { n: 1 | 2 | 3 }) {
  return <span className="poster-sq">SQ{n}</span>;
}

/** A finding heading, optionally tagged with the sub-question it answers. */
function Finding({ sq, children }: { sq?: 1 | 2 | 3; children: ReactNode }) {
  return (
    <h3 className="poster-finding">
      {sq && <SQ n={sq} />}
      {children}
    </h3>
  );
}

function BigStat({ value, label, small }: { value: string; label: ReactNode; small?: boolean }) {
  return (
    <div className={small ? "poster-stat small" : "poster-stat"}>
      <div className="poster-stat-value">{value}</div>
      <div className="poster-stat-label">{label}</div>
    </div>
  );
}

function ChartTitle({ children }: { children: ReactNode }) {
  return <p className="poster-chart-title">{children}</p>;
}

export default function Overview() {
  const { data: f, error, loading } = useApi(fetchFindings, []);
  const bars = BARS[useTheme().resolved];
  const datasets = rows(useApi(() => fetchPaperTable("datasets"), []).data);
  const transfer = rows(useApi(() => fetchPaperTable("generalise_month"), []).data);

  const ds = (key: string) => datasets.find((r) => r.key === key)?.values;
  const abl = f?.sq1.ablation;
  const sq2 = f?.sq2;
  const cmp = f?.sq3.comparison;
  const fpCut = sq2 ? Math.round(sq2.fp_reduction * 100) : null;
  const rfTransfer = transfer.find((r) => r.key === "random_forest")?.values.f1 ?? null;
  const transferRank =
    rfTransfer == null ? null : transfer.map((r) => r.values.f1 ?? 0).sort((a, b) => a - b).indexOf(rfTransfer);

  return (
    <div className="poster-sheet">
      <header className="poster-banner">
        <div className="poster-banner-text">
          <h1>
            A Hybrid Machine Learning Framework for Insider Threat Detection Using Behavioural
            Signals and Trust Modelling
          </h1>
          <p>
            <strong>Francois Scholtz</strong>
            <span aria-hidden>|</span>u19024232<span aria-hidden>|</span>Supervisor: Prof. Jan
            Eloff<span aria-hidden>|</span>Department of Computer Science, University of Pretoria
          </p>
        </div>
        <div className="poster-logo">
          <img src="/up-logo.png" alt="University of Pretoria" />
        </div>
      </header>

      <ApiStatus what="the results" loading={loading} error={error} />

      <div className="poster-grid">
        {/* ---- Column 1: Introduction, Methodology ---- */}
        <div className="poster-col">
          <Box title="Introduction" actions={[{ to: "/glossary", label: "Glossary" }]}>
            <p>
              Insiders already have authorised access, so harmful actions look like ordinary work.
              Rule-based monitoring misses gradual change and floods analysts with false alarms.
              Three gaps remain in the literature:
            </p>
            <ul>
              <li>Detection looks at one snapshot of activity, not behaviour over time.</li>
              <li>Trust is discussed but never measured or used in detection.</li>
              <li>Individual and hybrid models are not compared under identical conditions.</li>
            </ul>
            <p>
              <strong className="poster-label">Research question:</strong> How can behavioural
              signals over time, trust modelling and a fair comparison of strategies improve
              insider threat detection?
            </p>
            <p className="poster-tight">
              <strong className="poster-label">Aim:</strong>
            </p>
            <p>Build a five-layer framework and test it fairly on three synthetic datasets:</p>
            <ul className="poster-plain">
              <li>
                <SQ n={1} />
                Which signals over time reveal insiders?
              </li>
              <li>
                <SQ n={2} />
                Can a trust score cut false positives?
              </li>
              <li>
                <SQ n={3} />
                Do combined models beat single ones?
              </li>
            </ul>
          </Box>

          <Box
            title="Methodology"
            actions={[
              { to: "/framework", label: "Framework" },
              { to: "/data", label: "Data" },
            ]}
          >
            <ol className="poster-flow">
              {LAYERS.map((l, i) => (
                <li key={l.id}>
                  <Link to={`/framework#${l.id}`} className={i % 2 ? "alt" : undefined}>
                    <strong>
                      {i + 1}&nbsp;&nbsp;{l.title}
                    </strong>
                    <span>{l.text}</span>
                  </Link>
                </li>
              ))}
            </ol>
            <p className="poster-tight">
              <strong className="poster-label">Three datasets</strong>
            </p>
            <ul>
              <li>
                <strong>30-day logs:</strong> {ds("month")?.rows?.toLocaleString() ?? "3,000"}{" "}
                synthetic employee-days, 5 insider types
              </li>
              <li>
                <strong>Single-day logs:</strong>{" "}
                {ds("single_day")?.rows?.toLocaleString() ?? "14,000"} synthetic employee-days,
                slow drift
              </li>
              <li>
                <strong>Kaggle:</strong>{" "}
                {ds("raw_insider_threat")?.rows?.toLocaleString() ?? "299,880"} third-party synthetic
                employee-days (1,666 employees over 180 days)
              </li>
            </ul>
            <p className="poster-tight">
              <strong className="poster-label">Tools and metrics:</strong>
            </p>
            <ul>
              <li>Python, scikit-learn and PyTorch</li>
              <li>Precision, recall and F1, not accuracy</li>
            </ul>
          </Box>
        </div>

        <div className="poster-results">
          {/* Both Results columns end on the same line */}
          {/* ---- Column 2: Results: Time and trust ---- */}
          <div className="poster-col fill">
            <Box title="Results: Time and trust" actions={[{ to: "/results", label: "Results" }]}>
              <Finding sq={1}>History helps most on the Kaggle data</Finding>
              {abl && (
                <>
                  <div className="poster-stats">
                    <BigStat value={`+${f3(abl.kaggle.gain)}`} label="Mean F1 gain, Kaggle" />
                    <BigStat value={`+${f3(abl.month.gain)}`} label="Mean F1 gain, synthetic data" />
                  </div>
                  <ChartTitle>Mean F1 of nine strategies</ChartTitle>
                  <GroupedBars
                    data={[
                      { name: "30-day logs", snapshot: abl.month.snapshot_f1, history: abl.month.temporal_f1 },
                      { name: "Kaggle", snapshot: abl.kaggle.snapshot_f1, history: abl.kaggle.temporal_f1 },
                    ]}
                    category="name"
                    series={[
                      { key: "snapshot", label: "Single-day snapshot" },
                      { key: "history", label: "Multi-day history" },
                    ]}
                    colors={[bars.soft, bars.strong]}
                    domain={[0, 1]}
                    height={240}
                    hideValueAxis
                    paper
                  />
                </>
              )}
              <ul>
                <li>
                  All nine strategies ranked better on Kaggle with history. Mean average precision
                  rose from 0.629 to 0.705.
                </li>
                <li>
                  Real anomalies are unusual for that employee, which only a rolling baseline can
                  see.
                </li>
                <li>
                  The SVM gained the most (0.178 to 0.567) and the random forest gained 0.175 (0.608
                  to 0.783).
                </li>
              </ul>

              <Finding sq={2}>Trust works as a threshold, not a feature</Finding>
              {sq2 && (
                <>
                  <ChartTitle>Mean false positives per fold</ChartTitle>
                  <GroupedBars
                    data={[
                      { name: "No trust", fp: sq2.arms.no_trust.false_positive_count },
                      { name: "Trust as feature", fp: sq2.arms.trust_as_feature.false_positive_count },
                      { name: "Trust as threshold", fp: sq2.arms.trust_as_sensitivity.false_positive_count },
                    ]}
                    category="name"
                    series={[{ key: "fp", label: "Mean false positives per fold" }]}
                    colors={[bars.strong]}
                    height={210}
                    hideValueAxis
                    paper
                  />
                  <p>
                    <strong className="poster-highlight">{fpCut}% fewer false positives</strong> per
                    fold ({f3(sq2.arms.trust_as_feature.false_positive_count)} to{" "}
                    {f3(sq2.arms.trust_as_sensitivity.false_positive_count)}). Precision rose from{" "}
                    {f3(sq2.arms.trust_as_feature.precision)} to{" "}
                    {f3(sq2.arms.trust_as_sensitivity.precision)}. Recall fell from{" "}
                    {f3(sq2.arms.trust_as_feature.recall)} to{" "}
                    {f3(sq2.arms.trust_as_sensitivity.recall)}.
                  </p>
                  <ul>
                    <li>
                      As a model input, trust changed nothing because it is built from deviations
                      the model already sees.
                    </li>
                    <li>
                      Average precision stayed at {f3(sq2.arms.trust_as_sensitivity.pr_auc)} in
                      both designs, so the model ranks days the same and only the cut-off moves.
                    </li>
                  </ul>
                </>
              )}
            </Box>
          </div>

          {/* ---- Column 3: Results: Model choice ---- */}
          <div className="poster-col fill">
            <Box
              title="Results: Model choice"
              actions={[
                { to: "/results", label: "Results" },
                { to: "/models", label: "Models" },
                { to: "/compare", label: "Compare" },
              ]}
            >
              <Finding sq={3}>No hybrid beat the best single model</Finding>
              {cmp && (
                <>
                  <ChartTitle>F1 by dataset</ChartTitle>
                  <GroupedBars
                    data={(
                      [
                        ["30-day", cmp.month],
                        ["Single-day", cmp.single_day],
                        ["Kaggle", cmp.kaggle],
                      ] as const
                    ).map(([name, c]) => ({
                      name,
                      best: c.best_f1,
                      combined: c.combined_mean,
                      individual: c.individual_mean,
                    }))}
                    category="name"
                    series={[
                      { key: "best", label: "Random forest (best)" },
                      { key: "combined", label: "Combined, mean" },
                      { key: "individual", label: "Individual, mean" },
                    ]}
                    colors={[bars.strong, bars.mid, bars.soft]}
                    domain={[0, 1]}
                    height={270}
                    hideValueAxis
                    paper
                  />
                </>
              )}
              <ul>
                <li>
                  Within each dataset, combined strategies have the better average, but none beat
                  the random forest.
                </li>
                <li>
                  The random forest beat all fourteen rivals significantly on single-day and Kaggle
                  data, and tied with two ensembles on the 30-day logs.
                </li>
                <li>The random forest scored highest, but combined models avoid the worst failures.</li>
              </ul>

              <Finding>Scores do not transfer between organisations</Finding>
              {f && (
                <div className="poster-stats">
                  <BigStat value={f3(f.sq3.comparison.kaggle.best_f1)} label="Best F1, cross-validated on Kaggle" />
                  <BigStat
                    value={f3(f.sq3.transfer.month.best_f1)}
                    label="Best F1, trained on synthetic data, tested on Kaggle"
                  />
                </div>
              )}
              <ul>
                {rfTransfer != null && (
                  <li>
                    The random forest fell to{" "}
                    {transferRank === 1 ? "second-worst" : transferRank === 0 ? "worst" : "near the bottom"}{" "}
                    ({f3(rfTransfer)}).
                  </li>
                )}
                <li>The isolation forest, trained on benign data only, transferred most consistently.</li>
                <li>Best average precision after transfer was 0.139 and 0.163, against 0.025 by chance.</li>
              </ul>

              <Finding>SMOTE helps, under-sampling hurts</Finding>
              {f?.imbalance && (
                <>
                  <div className="poster-stats three">
                    <BigStat small value={f3(f.imbalance.none.f1)} label={<>Mean F1<br />Weights only</>} />
                    <BigStat small value={f3(f.imbalance.smote.f1)} label={<>Mean F1<br />With SMOTE</>} />
                    <BigStat small value={f3(f.imbalance.undersample.f1)} label={<>Mean F1<br />Under-sampling</>} />
                  </div>
                  <ul>
                    <li>SMOTE improved 11 of 15 strategies, most of all the CNN-RNN hybrid (+0.259).</li>
                    <li>
                      Under-sampling raised recall to {f3(f.imbalance.undersample.recall)} but cut
                      precision to {f3(f.imbalance.undersample.precision)}.
                    </li>
                  </ul>
                </>
              )}
            </Box>
          </div>
        </div>

        {/* ---- Column 4: Conclusions, Acknowledgements, Contact ---- */}
        <div className="poster-col">
          <Box title="Conclusions" actions={[{ to: "/findings", label: "Findings" }]}>
            <p>
              <strong className="poster-label">Answer to the research question:</strong> The
              framework improves detection when it observes behaviour over time and applies trust
              in the decision rule.
            </p>
            <ul className="poster-plain poster-conclusions">
              <li>
                <SQ n={1} />
                <strong>History beats snapshots.</strong> Multi-day baselines added{" "}
                {abl ? f3(abl.kaggle.gain) : "…"} mean F1 on the Kaggle data.
              </li>
              <li>
                <SQ n={1} />
                <strong>Off-hours access matters most.</strong> It was the strongest single signal
                {f?.sq1.top_signal ? ` (importance ${f3(f.sq1.top_signal.importance)})` : ""} on
                the 30-day logs.
              </li>
              <li>
                <SQ n={2} />
                <strong>Trust belongs in the decision rule.</strong> A threshold set for each
                employee cut false positives by {fpCut ?? "…"}%.
              </li>
              <li>
                <SQ n={3} />
                <strong>A single model won and hybrids are insurance.</strong> The random forest
                was best on all three datasets. Combined models raise the average, not the best
                score.
              </li>
              <li>
                <span className="poster-sq">•</span>
                <strong>Test beyond one organisation.</strong> Scores from cross-validation more
                than halved on unseen data.
              </li>
            </ul>
            <div className="poster-aside">
              <strong>Limitations:</strong>
              <ul>
                <li>Two of three datasets are synthetic</li>
                <li>The Kaggle data has no email or login signals</li>
                <li>Every model had the same small training budget</li>
              </ul>
              <strong>Future work:</strong>
              <ul>
                <li>Train on pooled data from several organisations</li>
                <li>Pair a supervised model with an anomaly detector for unfamiliar behaviour</li>
                <li>Tune the trust settings against the cost of a missed insider</li>
              </ul>
            </div>
          </Box>

          <Box title="Acknowledgements">
            <p>
              <strong className="poster-label">Prof. Jan Eloff</strong> for supervising this
              research.
            </p>
            <p>Department of Computer Science, University of Pretoria.</p>
            <p>Third-party synthetic data: Kaggle insider-threat dataset (classified environment).</p>
          </Box>

          <Box title="Contact">
            <p>
              <strong className="poster-label">Francois Scholtz</strong>
            </p>
            <p>
              <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
              <br />
              <a href={`tel:${CONTACT_PHONE.replace(/\s/g, "")}`}>{CONTACT_PHONE}</a>
            </p>
            <p>Supervisor: Prof. Jan Eloff</p>
            <p>Department of Computer Science, University of Pretoria</p>
          </Box>
        </div>
      </div>
    </div>
  );
}
