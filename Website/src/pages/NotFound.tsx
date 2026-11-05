import { Link } from "react-router-dom";
import { PageHeader } from "../components/ui";

export default function NotFound() {
  return (
    <>
      <PageHeader title="Page not found" />
      <p className="muted">
        <Link to="/">Back to the overview</Link>
      </p>
    </>
  );
}
