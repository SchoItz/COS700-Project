// The site is static: every response the dashboard's backend would return was
// exported to JSON under public/data (webapp/backend/export_static.py in the
// framework), at the same path as its API route.

/** Thrown for a file that does not exist, in the shape `useApi` checks for 404. */
class NotFound extends Error {
  response = { status: 404 };
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`/data/${path}.json`);
  const type = response.headers.get("content-type") ?? "";
  // A missing file is answered with the app's index.html, not JSON.
  if (!response.ok || !type.includes("json")) throw new NotFound(`Not found: ${path}`);
  return (await response.json()) as T;
}

// --------------------------------------------------------------------------
// Tables: the same structure the backend renders to LaTeX for the paper
// (framework/reporting/tables.py), so a table here and in the report are two
// views of one object.
// --------------------------------------------------------------------------

export interface Cell {
  text: string;
  bold: boolean;
}

export interface Header {
  text: string;
  span: number;
}

export interface Row {
  label: Cell;
  cells: Cell[];
  key: string | null;
  values: Record<string, number | null>;
}

export interface Section {
  rows: Row[];
  title: string | null;
}

export interface Table {
  name: string;
  caption: string;
  align: string;
  header: Header[][];
  sections: Section[];
}

export type PaperTable = (Table & { available: true }) | { name: string; available: false };

export interface Experiment {
  id: string;
  dataset: string;
  question: string;
  tables: string[];
}

export const fetchExperiments = () =>
  get<Experiment[]>("paper/experiments");

export const fetchPaperTable = (name: string) =>
  get<PaperTable>(`paper/tables/${name}`);

// --------------------------------------------------------------------------
// Dataset details and the weekday corpus
// --------------------------------------------------------------------------

export interface MonthDetails {
  total_records: number;
  n_employees: number;
  n_days: number;
  n_insider_threats: number;
  archetypes: Record<string, string[]>;
}

export interface KaggleDetails {
  total_records: number;
  n_employees: number;
  n_malicious_days: number;
  n_malicious_employees: number;
  date_range: { start: string; end: string };
  departments: string[];
}

export const fetchMonthDetails = () =>
  get<MonthDetails>("datasets/month");

export const fetchKaggleDetails = () =>
  get<KaggleDetails>("datasets/raw_insider_threat");

export interface CorpusSummary {
  total_records: number;
  n_employees: number;
  n_drifted_employees: number;
  n_files: number;
  n_weeks: number;
  date_range: { start: string; end: string };
}

export interface WeekdayCount {
  day: string;
  records: number;
}

export interface ActivityAverageRow {
  day: string;
  group: "benign" | "drifted";
  [metric: string]: number | string;
}

export interface DriftTrendRow {
  week_number: number;
  benign: number;
  drifted: number;
}

export interface Employee {
  employee_id: string;
  department: string;
  role: string;
  drifted: boolean;
  total_events: number;
}

export const fetchCorpusSummary = () =>
  get<CorpusSummary>("corpus/summary");

export const fetchWeekdayCounts = () =>
  get<WeekdayCount[]>("corpus/weekday-counts");

export const fetchActivityAverages = () =>
  get<ActivityAverageRow[]>("corpus/activity-averages");

export const fetchDriftTrend = (metric: string, day: string) =>
  get<DriftTrendRow[]>(`corpus/drift-trend/${metric}/${day}`);

export const fetchEmployees = () =>
  get<Employee[]>("corpus/employees");

// --------------------------------------------------------------------------
// Models (the detection strategies)
// --------------------------------------------------------------------------

export interface ModelSummary {
  name: string;
  title: string;
  kind: "classical" | "deep" | "ensemble" | "hybrid";
  family: "individual" | "combined";
  paradigm: "anomaly" | "misuse";
  summary: string;
}

export interface Metrics {
  f1: number | null;
  precision: number | null;
  recall: number | null;
  false_positive_rate: number | null;
  pr_auc: number | null;
  false_positive_count: number | null;
}

export interface Significance {
  is_best: boolean;
  p_value?: number;
  significant?: boolean;
  mean_diff_vs_best?: number;
}

export type RankedResult = Metrics & {
  experiment: string;
  dataset: string;
  rank: number;
  of: number;
  significance?: Significance | null;
};

export type VariantResult = Metrics & { variant: string };

export interface ModelDetail extends ModelSummary {
  details: string[];
  imbalance: string;
  cross_validation: RankedResult[];
  generalisation: RankedResult[];
  ablation: { experiment: string; dataset: string; arms: VariantResult[] }[];
  trust: VariantResult[];
  resampling: VariantResult[];
}

export const fetchModels = () => get<ModelSummary[]>("models");

export const fetchModel = (name: string) =>
  get<ModelDetail>(`models/${name}`);

// --------------------------------------------------------------------------
// Framework, findings, comparison, alerts
// --------------------------------------------------------------------------

export interface FrameworkInfo {
  temporal: { window: number; min_periods: number };
  trust: {
    decay_rate: number;
    recovery_rate: number;
    deviation_threshold: number;
    initial_trust: number;
    base_threshold: number;
    sensitivity_gain: number;
    threshold_bounds: [number, number];
    ensemble_gain: number;
  };
  detection: { n_strategies: number; n_individual: number; n_combined: number; deep_epochs: number };
  validation: {
    n_splits: number;
    seed: number;
    decision_threshold: number;
    alpha: number;
    min_minority_for_smote: number;
    kaggle_sample: { n_malicious_employees: number; n_benign_employees: number };
  };
}

export const fetchFramework = () => get<FrameworkInfo>("framework");

type Arm = {
  f1: number;
  precision: number;
  recall: number;
  pr_auc: number;
  false_positive_count: number;
  false_positive_rate: number;
};

interface FamilyComparison {
  label: string;
  best: string;
  best_f1: number;
  best_family: "individual" | "combined";
  individual_mean: number;
  combined_mean: number;
  best_individual: number;
  best_combined: number;
}

export interface Findings {
  sq1: {
    ablation: Record<string, { snapshot_f1: number; temporal_f1: number; gain: number }>;
    signal_shares: Record<string, number>;
    top_signal: { feature: string; importance: number } | null;
  };
  sq2?: { arms: Record<string, Arm>; fp_reduction: number };
  sq3: {
    comparison: Record<string, FamilyComparison>;
    transfer: Record<string, FamilyComparison>;
  };
  imbalance?: Record<string, { f1: number; precision: number; recall: number }>;
}

export const fetchFindings = () => get<Findings>("findings");

export interface CompareData {
  metric: string;
  metrics: Record<string, string>;
  columns: { id: string; label: string }[];
  models: { name: string; family: "individual" | "combined"; scores: Record<string, number | null> }[];
}

export const fetchCompare = (metric: string) =>
  get<CompareData>(`compare/${metric}`);

export interface AlertList {
  dataset: string;
  total: number;
  malicious: number;
  rows: {
    user_id: string;
    timestamp: string;
    score: number;
    threshold: number;
    trust_score: number;
    label: number;
  }[];
}

/** The exported lists hold the top 100 alerts. */
export const fetchAlerts = (dataset: string) => get<AlertList>(`alerts/${dataset}`);
