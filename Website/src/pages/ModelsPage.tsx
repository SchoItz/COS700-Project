import { fetchModels, type ModelSummary } from "../api";
import { ApiStatus, Badge, CardLink, PageHeader, ParadigmBadge } from "../components/ui";
import { useApi } from "../hooks/useApi";

const KIND_LABEL: Record<ModelSummary["kind"], string> = {
  classical: "Classical",
  deep: "Deep learning",
  ensemble: "Ensemble",
  hybrid: "Deep hybrid",
};

const GROUPS = [
  { family: "individual", title: "Individual models", grid: "models-grid-3" },
  { family: "combined", title: "Combined and hybrid models", grid: "models-grid-2" },
] as const;

export default function ModelsPage() {
  const { data, error, loading } = useApi(fetchModels, []);
  const models = data ?? [];

  return (
    <>
      <PageHeader
        title="Models"
        lead="The fifteen detection strategies compared in the report, all evaluated on the same feature matrix, folds and decision rule. Open one to see how it is built and how it performed on every dataset."
      />
      <ApiStatus what="the models" loading={loading} error={error} />
      <div className="models-layout">
      {GROUPS.map((g) => (
        <section key={g.family} className="section">
          <h2>{g.title}</h2>
          <div className={`card-grid ${g.grid}`}>
            {models
              .filter((m) => m.family === g.family)
              .map((m) => (
                <CardLink
                  key={m.name}
                  to={`/model/${m.name}`}
                  title={m.title}
                  top={
                    <>
                      <Badge>{KIND_LABEL[m.kind]}</Badge>
                      <ParadigmBadge paradigm={m.paradigm} />
                    </>
                  }
                >
                  <p className="muted">{m.summary}</p>
                </CardLink>
              ))}
          </div>
        </section>
      ))}
      </div>
    </>
  );
}
