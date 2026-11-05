import { PageHeader } from "../components/ui";

const TERMS: [string, string][] = [
  ["Precision (P)", "Of the employee-days the model flagged, the share that were genuinely malicious. Low precision means alert fatigue."],
  ["Recall (R)", "Of the genuinely malicious employee-days, the share the model flagged. Also called detection rate."],
  ["F1", "The harmonic mean of precision and recall. It punishes a model that is strong on one and weak on the other."],
  ["False-positive rate (FPR)", "The share of benign employee-days that were wrongly flagged."],
  ["FP (false positives)", "The mean count of benign days wrongly flagged per fold. For the generalisation experiments, the total over the whole test set."],
  ["PR-AUC (average precision)", "The area under the precision-recall curve. It measures how well a model ranks malicious days above benign ones, independent of any cut-off."],
  ["Accuracy", "Not reported as a headline. A detector that never fires can exceed 95% accuracy when malicious days are this rare."],
  ["Cross-validation", "Ten stratified folds sharing one seed: each fold is held out once, and every strategy sees identical folds."],
  ["Wilcoxon signed-rank test", "A paired test over the per-fold scores of two strategies. It makes no normality assumption."],
  ["Holm-Bonferroni correction", "Adjusts the significance threshold for comparing one strategy against fourteen others, so chance alone does not produce false positives."],
  ["Anomaly-based", "Learns what normal looks like from benign data only, and flags what does not fit (isolation forest, autoencoder)."],
  ["Misuse-based", "Learns from labelled malicious examples (every other strategy)."],
  ["Individual / combined", "A single model, versus an ensemble or hybrid that combines several."],
  ["Trust score", "A per-employee value in [0, 1] that falls under sustained anomalous behaviour and recovers during normal activity."],
  ["Snapshot vs temporal", "Snapshot uses each day's raw features only. Temporal adds the deviation-from-baseline features and the trust score, which need multi-day history."],
  ["SMOTE", "Synthesises extra minority-class rows by interpolation. Applied to training folds only."],
  ["Generalisation", "Training on one dataset and testing on another the model has never seen."],
];

export default function GlossaryPage() {
  return (
    <>
      <PageHeader title="Glossary" lead="The terms and metrics used in the report's tables." />
      <div className="panel">
        <dl className="glossary">
          {TERMS.map(([term, definition]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd>{definition}</dd>
            </div>
          ))}
        </dl>
      </div>
    </>
  );
}
