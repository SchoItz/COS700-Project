/** Small presentational building blocks shared by every page. */
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function PageHeader({
  title,
  eyebrow,
  crumbs,
  lead,
  children,
}: {
  title: ReactNode;
  eyebrow?: ReactNode;
  crumbs?: ReactNode;
  lead?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <header className="page-header">
      {crumbs && <p className="crumbs">{crumbs}</p>}
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      {lead && <p className="lead muted">{lead}</p>}
      {children}
    </header>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="status loading" role="status">
      <span className="spinner" aria-hidden /> {label}
    </div>
  );
}

export function ErrorMessage({ what, error }: { what: string; error: string }) {
  return (
    <div className="status error" role="alert">
      Could not load {what}: {error}.
    </div>
  );
}

/** Loading spinner or error message for one API call; renders nothing once
 * the data has arrived. */
export function ApiStatus({ what, loading, error }: { what: string; loading: boolean; error: string | null }) {
  if (error) return <ErrorMessage what={what} error={error} />;
  if (loading) return <Loading />;
  return null;
}

type Tone = "blue" | "green" | "red" | "amber";

export function Badge({ tone = "blue", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function ParadigmBadge({ paradigm }: { paradigm: string }) {
  return paradigm === "anomaly" ? (
    <Badge tone="amber">Anomaly-based</Badge>
  ) : (
    <Badge tone="green">Misuse-based</Badge>
  );
}

export function CardLink({ to, title, top, children }: { to: string; title: ReactNode; top?: ReactNode; children?: ReactNode }) {
  return (
    <Link to={to} className="card">
      {top && <div className="card-top">{top}</div>}
      <h3>{title}</h3>
      {children}
    </Link>
  );
}

export function Stat({ value, label, wide }: { value: ReactNode; label: ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? "stat-card wide" : "stat-card"}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

interface Step {
  to: string;
  label: string;
}

export function PrevNext({ prev, next }: { prev?: Step; next?: Step }) {
  return (
    <nav className="prev-next" aria-label="Previous and next">
      {prev ? <Link to={prev.to}>← {prev.label}</Link> : <span />}
      {next ? <Link to={next.to}>{next.label} →</Link> : <span />}
    </nav>
  );
}
