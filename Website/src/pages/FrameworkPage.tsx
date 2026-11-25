import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { fetchFramework, type FrameworkInfo } from "../api";
import { TrustWalk } from "../components/Charts";
import { ApiStatus, PageHeader } from "../components/ui";
import { useApi } from "../hooks/useApi";

/** The five layers as tabs: one layer is shown at a time, chosen by the URL
 * hash (/framework#trust), so links from other pages open the right layer. */

const LAYERS = [
  { id: "data", label: "Data" },
  { id: "temporal", label: "Temporal signals" },
  { id: "trust", label: "Trust" },
  { id: "detection", label: "Detection" },
  { id: "validation", label: "Validation" },
] as const;

type LayerId = (typeof LAYERS)[number]["id"];

/** An illustrative employee: ordinary days (deviation 0.8) with five anomalous
 * days (deviation 2.0) from day 8, run through the same recurrence and
 * threshold rule as framework/trust/trust_score.py, with its parameters. */
const DAYS = 40;
const ANOMALOUS: [number, number] = [8, 12];

function trustWalk(t: FrameworkInfo["trust"]) {
  const [lo, hi] = t.threshold_bounds;
  let trust = t.initial_trust;
  return Array.from({ length: DAYS }, (_, i) => {
    const day = i + 1;
    const deviation = day >= ANOMALOUS[0] && day <= ANOMALOUS[1] ? 2.0 : 0.8;
    const excess = deviation - t.deviation_threshold;
    trust += excess > 0 ? -t.decay_rate * excess : t.recovery_rate;
    trust = Math.min(Math.max(trust, 0), 1);
    const threshold = Math.min(Math.max(t.base_threshold + t.sensitivity_gain * (trust - 0.5), lo), hi);
    return { day, trust, threshold };
  });
}

function Params({ rows }: { rows: [string, string][] }) {
  return (
    <div className="table-scroll">
      <table>
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={k}>
              <td>{k}</td>
              <td>
                <code>{v}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Formula({ children }: { children: ReactNode }) {
  return <div className="formula">{children}</div>;
}

/** Two-column body on wide screens: the explanation, and a side column with
 * the parameters or a short summary. */
function LayerBody({ main, side }: { main: ReactNode; side: ReactNode }) {
  return (
    <div className="layer-body">
      <div className="layer-main">{main}</div>
      <aside className="layer-side">{side}</aside>
    </div>
  );
}

function DataLayer() {
  return (
    <LayerBody
      main={
        <>
          <p className="layer-lead">
            Load every source, map it onto one common schema, and clean it so that synthetic and
            third-party data flow through the same downstream layers unchanged.
          </p>
          <h3>The common schema</h3>
          <p>
            Every source is mapped onto seventeen columns: an employee identifier, a timestamp,
            the source and event type, department and role, two temporal flags (off-hours and
            weekend), eight activity counters and a binary malicious label. The eight counters
            are device activity, printing, email, file activity, HTTP requests, failed logins,
            data transferred (MB) and session duration (minutes).
          </p>
          <h3>Cleaning and merging</h3>
          <ul>
            <li>
              When sources are merged, duplicate records with the same employee, timestamp,
              event type and source are dropped.
            </li>
            <li>
              Conflicting labels for the same record resolve to <strong>malicious</strong>, so a
              duplicate benign row can never hide a positive observation.
            </li>
            <li>
              Missing numbers take the column median and missing categories the column mode.
              Categories are one-hot encoded and numbers are standardised.
            </li>
          </ul>
          <h3>Ethics and traceability</h3>
          <p>
            Origin country, citizenship and medical history are dropped if a source contains
            them. The employee identifier and timestamp are kept so every alert can be traced
            back, but they are never given to a model.
          </p>
        </>
      }
      side={
        <>
          <h3>In one line</h3>
          <p className="muted">Many sources in, one clean matrix out.</p>
          <Params
            rows={[
              ["Schema columns", "17"],
              ["Activity counters", "8"],
              ["Temporal flags", "off-hours, weekend"],
              ["Numeric imputation", "median"],
              ["Categorical imputation", "mode"],
            ]}
          />
          <div className="link-buttons">
            <Link to="/data" className="button-link">See the three datasets</Link>
          </div>
        </>
      }
    />
  );
}

function TemporalLayer({ info }: { info: FrameworkInfo | null }) {
  const w = info?.temporal.window ?? 14;
  return (
    <LayerBody
      main={
        <>
          <p className="layer-lead">
            Judge each day against what is normal <em>for that employee</em> and for their peers,
            instead of against one global rule.
          </p>
          <h3>Deviation from the employee&apos;s own baseline</h3>
          <p>
            For each employee and each of the eight counters, a rolling mean and standard
            deviation are taken over the {w} events <em>before</em> the one being scored. The day
            is then expressed as a standard score:
          </p>
          <Formula>
            z<sub>self</sub> = (x<sub>today</sub> − mean of previous {w}) ÷ standard deviation of
            previous {w}
          </Formula>
          <p>
            The current day is left out of its own baseline. If it were included, it would
            partly explain away the very deviation it is meant to measure.
          </p>
          <h3>Deviation from peers</h3>
          <p>
            A second score compares the employee with others in the same department and role on
            the same day. The self score catches a <em>change</em> in behaviour; the peer score
            catches behaviour that is unusual for the role even if the employee has always
            behaved that way.
          </p>
          <h3>What comes out</h3>
          <p>
            Eight counters × two comparisons give sixteen deviation features, plus one aggregate
            deviation magnitude (the mean absolute z-score) that feeds the trust layer. With one
            record per day, {w} events cover two weeks: long enough to smooth out daily noise,
            short enough for a sustained change to show.
          </p>
        </>
      }
      side={
        <>
          <h3>Settings used</h3>
          {info && (
            <Params
              rows={[
                ["Baseline window (events)", String(info.temporal.window)],
                ["Minimum prior observations", String(info.temporal.min_periods)],
                ["Deviation features", "16"],
              ]}
            />
          )}
          <p className="muted">
            Before {info?.temporal.min_periods ?? 3} prior events exist, and wherever the standard
            deviation is zero, the deviation is set to zero.
          </p>
          <div className="link-buttons">
            <Link to="/results/E4" className="button-link">Does multi-day history help?</Link>
          </div>
        </>
      }
    />
  );
}

function TrustLayer({ info }: { info: FrameworkInfo | null }) {
  const t = info?.trust;
  return (
    <LayerBody
      main={
        <>
          <p className="layer-lead">
            Turn deviation into a running trust score that captures how <em>long</em> an employee
            has been unusual, not just how unusual one day was.
          </p>
          <h3>How the score moves</h3>
          <p>
            Every employee starts at full trust (1.0). Their days are processed in time order:
          </p>
          <Formula>
            if deviation &gt; θ: trust ← trust − α × (deviation − θ)
            <br />
            otherwise: trust ← trust + ρ
            <br />
            then clip to [0, 1]
          </Formula>
          <p>
            Trust falls quickly during anomalous days and recovers slowly afterwards, so several
            unusual days in a row cost far more than a single one.
          </p>
          {t && (
            <figure className="chart-box">
              <figcaption>Worked example: one employee with five anomalous days</figcaption>
              <TrustWalk data={trustWalk(t)} anomalous={ANOMALOUS} />
              <p className="table-note">
                Illustrative input; the parameters are the ones used for the results.
              </p>
            </figure>
          )}
          <h3>Two ways to use it</h3>
          <ul>
            <li>
              <strong>Trust as a feature:</strong> the score is one more model input, and every
              strategy uses the same 0.5 cut-off.
            </li>
            <li>
              <strong>Trust as a threshold:</strong> the score also sets each employee&apos;s own
              alert cut-off. A trusted employee needs stronger evidence before an alert; one
              whose trust has dropped is alerted sooner. The cut-off is clipped so nobody becomes
              unalertable or permanently alerting.
            </li>
          </ul>
        </>
      }
      side={
        <>
          <h3>Settings used</h3>
          {t && (
            <Params
              rows={[
                ["Decay rate (α)", String(t.decay_rate)],
                ["Recovery rate (ρ)", String(t.recovery_rate)],
                ["Deviation threshold (θ)", String(t.deviation_threshold)],
                ["Initial trust", String(t.initial_trust)],
                ["Base alert threshold", String(t.base_threshold)],
                ["Sensitivity gain (γ)", String(t.sensitivity_gain)],
                ["Threshold bounds", `${t.threshold_bounds[0]} to ${t.threshold_bounds[1]}`],
                ["Trust-weighted ensemble gain (λ)", String(t.ensemble_gain)],
              ]}
            />
          )}
          <p className="muted">
            Per-employee threshold = 0.5 + γ × (trust − 0.5), clipped to the bounds.
          </p>
          <div className="link-buttons">
            <Link to="/results/E8" className="button-link">Does trust reduce false positives?</Link>
          </div>
        </>
      }
    />
  );
}

function DetectionLayer({ info }: { info: FrameworkInfo | null }) {
  const d = info?.detection;
  return (
    <LayerBody
      main={
        <>
          <p className="layer-lead">
            Score every employee-day with {d?.n_strategies ?? 15} strategies that all share one
            interface, one feature matrix, one set of folds and one decision rule.
          </p>
          <h3>The strategies</h3>
          <ul>
            <li>
              <strong>Individual, misuse-based:</strong> logistic regression, decision tree,
              random forest, support vector machine, LSTM, 1-D convolutional network and graph
              convolutional network.
            </li>
            <li>
              <strong>Individual, anomaly-based:</strong> isolation forest and autoencoder, both
              trained on benign data only.
            </li>
            <li>
              <strong>Combined:</strong> gradient boosting, soft-voting ensemble, stacking
              ensemble, CNN-RNN hybrid, autoencoder-RNN hybrid and a trust-weighted ensemble that
              damps scores for high-trust employees.
            </li>
          </ul>
          <h3>A fair comparison</h3>
          <p>
            Every strategy gets the same budget: the deep models all train for{" "}
            {d?.deep_epochs ?? 12} epochs with the same optimiser and learning rate, and no
            strategy is tuned more than another, since uneven tuning would confound the result.
          </p>
          <h3>Class imbalance</h3>
          <p>
            Malicious days are rare, so supervised models weight the minority class. On top of
            that, SMOTE and 3:1 under-sampling are tested. Resampling only ever touches the
            training fold, after the split; doing it before would leak synthetic copies of
            test-fold positives into training and inflate every score.
          </p>
        </>
      }
      side={
        <>
          <h3>Settings used</h3>
          {info && (
            <Params
              rows={[
                ["Strategies", String(info.detection.n_strategies)],
                ["Individual / combined", `${info.detection.n_individual} / ${info.detection.n_combined}`],
                ["Training epochs (deep models)", String(info.detection.deep_epochs)],
                ["Minimum minority rows for SMOTE", String(info.validation.min_minority_for_smote)],
              ]}
            />
          )}
          <p className="muted">
            Common interface: <code>fit</code>, <code>predict_proba</code>, <code>predict</code>.
          </p>
          <div className="link-buttons">
            <Link to="/models" className="button-link">See all fifteen models</Link>
            <Link to="/results/E9" className="button-link">Class imbalance results</Link>
          </div>
        </>
      }
    />
  );
}

function ValidationLayer({ info }: { info: FrameworkInfo | null }) {
  const v = info?.validation;
  return (
    <LayerBody
      main={
        <>
          <p className="layer-lead">
            Measure performance in a way that is honest about rare events, and turn scores into
            an alert list an analyst could act on.
          </p>
          <h3>Why not accuracy?</h3>
          <p>
            A detector that never raises an alert would score over 95% accuracy on these
            datasets. Instead the framework reports precision, recall, F1, detection rate and
            false-positive rate, plus average precision (the area under the precision-recall
            curve), which does not depend on any threshold.
          </p>
          <h3>Paired, tested comparisons</h3>
          <p>
            Stratified {v?.n_splits ?? 10}-fold cross-validation with one fixed seed gives every
            strategy the same folds, so results are paired. Each strategy is tested against the
            best with the Wilcoxon signed-rank test, and the Holm-Bonferroni correction accounts
            for comparing fourteen rivals at once.
          </p>
          <h3>Why ten folds</h3>
          <p>
            With five folds the smallest possible p-value is 0.0625, so after correction no
            difference could ever be significant. Ten folds bring it to 0.00195, below the
            strictest corrected threshold (about 0.0036).
          </p>
          <h3>Alert output</h3>
          <p>
            The layer&apos;s operational output is a ranked alert list. Each row is scored by a
            model that never trained on it, and the trust-based threshold decides which days
            become alerts.
          </p>
        </>
      }
      side={
        <>
          <h3>Settings used</h3>
          {v && (
            <Params
              rows={[
                ["Cross-validation folds", String(v.n_splits)],
                ["Seed", String(v.seed)],
                ["Global decision threshold", String(v.decision_threshold)],
                ["Significance level (α)", String(v.alpha)],
                [
                  "Kaggle sample",
                  `${v.kaggle_sample.n_malicious_employees} malicious + ${v.kaggle_sample.n_benign_employees} benign employees`,
                ],
              ]}
            />
          )}
          <div className="link-buttons">
            <Link to="/glossary" className="button-link">What each metric means</Link>
            <Link to="/alerts/month" className="button-link">See a ranked alert list</Link>
            <Link to="/results" className="button-link">All results</Link>
          </div>
        </>
      }
    />
  );
}

export default function FrameworkPage() {
  const { data: info, error, loading } = useApi(fetchFramework, []);
  const { hash } = useLocation();
  const active: LayerId = LAYERS.find((l) => `#${l.id}` === hash)?.id ?? "data";
  const index = LAYERS.findIndex((l) => l.id === active);
  const prev = LAYERS[index - 1];
  const next = LAYERS[index + 1];

  return (
    <>
      <PageHeader
        title="The framework"
        lead="Five layers, each with one job and a defined hand-over to the next, so the contribution of each can be measured on its own. Choose a layer to read how it works. Settings are read from the code, so they are the ones the results were produced with."
      />

      <nav className="layer-flow" aria-label="The five layers">
        {LAYERS.map((l, i) => (
          <Link
            key={l.id}
            to={{ hash: l.id }}
            replace
            className={l.id === active ? "layer-box active" : "layer-box"}
            aria-current={l.id === active ? "true" : undefined}
          >
            <span className="nav-id">{i + 1}</span>
            {l.label}
          </Link>
        ))}
      </nav>

      <ApiStatus what="the framework settings" loading={loading} error={error} />

      <section className="panel layer-panel" id={active}>
        <h2>
          {index + 1}. {LAYERS[index].label} layer
        </h2>
        {active === "data" && <DataLayer />}
        {active === "temporal" && <TemporalLayer info={info} />}
        {active === "trust" && <TrustLayer info={info} />}
        {active === "detection" && <DetectionLayer info={info} />}
        {active === "validation" && <ValidationLayer info={info} />}
      </section>

      <nav className="prev-next" aria-label="Previous and next layer">
        {prev ? (
          <Link to={{ hash: prev.id }} replace>
            ← {prev.label}
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link to={{ hash: next.id }} replace>
            {next.label} →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </>
  );
}
