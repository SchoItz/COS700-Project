/** Human labels for the report's tables, keyed by the table names the backend
 * serves (`framework.paper.TABLES`). Labels only: every number on a page comes
 * from the backend, so nothing here can drift from the report. */
export const TABLE_LABELS: Record<string, { title: string; section: string }> = {
  datasets: { title: "Datasets", section: "Experimental setup" },
  results_month: { title: "Strategy comparison", section: "E1 results" },
  significance_month: { title: "Significance tests", section: "E1 results" },
  results_single_day: { title: "Strategy comparison", section: "E2 results" },
  significance_single_day: { title: "Significance tests", section: "E2 results" },
  results_kaggle: { title: "Strategy comparison", section: "E3 results" },
  significance_kaggle: { title: "Significance tests", section: "E3 results" },
  ablation_month: { title: "Snapshot vs temporal history", section: "E4 results" },
  ablation_kaggle: { title: "Snapshot vs temporal history", section: "E5 results" },
  generalise_month: { title: "Transfer to Kaggle", section: "E6 results" },
  generalise_single_day: { title: "Transfer to Kaggle", section: "E7 results" },
  trust_designs: { title: "Trust integration designs", section: "E8 results" },
  imbalance: { title: "Class-imbalance treatments", section: "E9 results" },
  signal_importance: { title: "Signal importance", section: "E10 results" },
};

export const EXPERIMENT_TITLES: Record<string, string> = {
  DS: "Datasets",
  E1: "Strategy comparison, 30-day logs",
  E2: "Strategy comparison, single-day logs",
  E3: "Strategy comparison, Kaggle",
  E4: "Temporal ablation, 30-day logs",
  E5: "Temporal ablation, Kaggle",
  E6: "Generalisation from 30-day logs",
  E7: "Generalisation from single-day logs",
  E8: "Trust integration",
  E9: "Class imbalance",
  E10: "Signal importance",
};

/** One plain-language sentence per experiment, matching the paper's reading
 * of it. The numbers themselves are in the chart and table below it. */
export const TAKEAWAYS: Record<string, string> = {
  E1: "The random forest is the best strategy. Combined strategies have the better average, but none beat it.",
  E2: "The hardest dataset, with gradual drift. The random forest is again best, and combined strategies again have the better average.",
  E3: "On the Kaggle data the random forest is still best; combined strategies again lift the average, not the top score.",
  E4: "Multi-day history adds very little here: the synthetic anomalies are already extreme in their raw values.",
  E5: "On the Kaggle data history clearly helps: mean F1 rises and almost every strategy improves once it can compare a day with that employee's own past.",
  E6: "Trained on synthetic data and tested on Kaggle, every score collapses and the ranking changes almost completely; the random forest falls near the bottom.",
  E7: "The same transfer test from single-day data: scores stay low, and the isolation forest, trained on benign data only, transfers best.",
  E8: "Trust as a model input changes nothing. Used as a per-employee alert threshold, it cuts false positives sharply, at some cost in recall.",
  E9: "SMOTE improves on class weighting alone; under-sampling raises recall but costs so much precision that F1 drops.",
  E10: "Off-hours access is by far the strongest single signal; raw daily values carry most of the importance.",
};

export const tableTitle = (name: string) => TABLE_LABELS[name]?.title ?? name;

/** The results grouped by the question they answer, as the paper's Results and
 * Discussion sections do, rather than by experiment number. */
export interface Theme {
  id: string;
  title: string;
  question: string;
  experiments: string[];
}

export const THEMES: Theme[] = [
  {
    id: "compare",
    title: "Which strategy is best?",
    question: "How do the fifteen strategies compare under cross-validation, on three datasets?",
    experiments: ["E1", "E2", "E3"],
  },
  {
    id: "history",
    title: "Does multi-day history help?",
    question: "Does observing behaviour over time beat a single-day snapshot?",
    experiments: ["E4", "E5"],
  },
  {
    id: "transfer",
    title: "Do the strategies generalise?",
    question: "How well does a strategy trained on one dataset detect threats in one it never saw?",
    experiments: ["E6", "E7"],
  },
  {
    id: "trust",
    title: "Does trust reduce false positives?",
    question: "Which way of using the trust score works, and does it help at all?",
    experiments: ["E8"],
  },
  {
    id: "imbalance",
    title: "How should class imbalance be handled?",
    question: "Does SMOTE or under-sampling improve on class weighting alone?",
    experiments: ["E9"],
  },
  {
    id: "signals",
    title: "Which signals matter?",
    question: "Which behavioural signals does the detection actually rest on?",
    experiments: ["E10"],
  },
];
