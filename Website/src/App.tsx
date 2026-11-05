import { lazy } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./layout/Layout";

// Each page is its own chunk, loaded when first visited.
const AlertsPage = lazy(() => import("./pages/AlertsPage"));
const ComparePage = lazy(() => import("./pages/ComparePage"));
const CorpusPage = lazy(() => import("./pages/CorpusPage"));
const DataPage = lazy(() => import("./pages/DataPage"));
const FindingsPage = lazy(() => import("./pages/FindingsPage"));
const FrameworkPage = lazy(() => import("./pages/FrameworkPage"));
const GlossaryPage = lazy(() => import("./pages/GlossaryPage"));
const ModelPage = lazy(() => import("./pages/ModelPage"));
const ModelsPage = lazy(() => import("./pages/ModelsPage"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Overview = lazy(() => import("./pages/Overview"));
const ResultsPage = lazy(() => import("./pages/ResultsPage"));
const LegacyResultsRedirect = lazy(() =>
  import("./pages/ResultsPage").then((m) => ({ default: m.LegacyResultsRedirect })),
);

const ROUTES = [
  { path: "experiment/:id", page: LegacyResultsRedirect },
  { path: "table/:name", page: LegacyResultsRedirect },
  { path: "models", page: ModelsPage },
  { path: "model/:name", page: ModelPage },
  { path: "data", page: DataPage },
  { path: "data/corpus", page: CorpusPage },
  { path: "framework", page: FrameworkPage },
  { path: "results", page: ResultsPage },
  { path: "results/:id", page: ResultsPage },
  { path: "findings", page: FindingsPage },
  { path: "compare", page: ComparePage },
  { path: "alerts/:dataset", page: AlertsPage },
  { path: "glossary", page: GlossaryPage },
  { path: "*", page: NotFound },
];

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        {ROUTES.map(({ path, page: Page }) => (
          <Route key={path} path={path} element={<Page />} />
        ))}
      </Route>
    </Routes>
  );
}
