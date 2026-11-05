import { Suspense, useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { fetchExperiments, type Experiment } from "../api";
import { Loading } from "../components/ui";
import { useApi } from "../hooks/useApi";
import ThemeToggle from "./ThemeToggle";

export interface LayoutContext {
  experiments: Experiment[];
}

const NAV = [
  { to: "/framework", label: "Framework" },
  { to: "/data", label: "Data" },
  { to: "/results", label: "Results" },
  { to: "/models", label: "Models" },
  { to: "/compare", label: "Compare" },
  { to: "/findings", label: "Findings" },
];

/** Older experiment and table links count as part of Results. */
const RESULTS_PATHS = ["/results", "/experiment", "/table", "/alerts"];

export default function Layout() {
  const { data } = useApi(fetchExperiments, []);
  const experiments = data ?? [];
  const [menuOpen, setMenuOpen] = useState(false); // narrow screens: the whole nav
  const { pathname, hash } = useLocation();

  useEffect(() => {
    setMenuOpen(false);
    if (!hash) window.scrollTo(0, 0);
  }, [pathname, hash]);

  return (
    <div className="shell">
      <header className="navbar">
        <div className="navbar-inner">
          <NavLink to="/" end className="brand">
            <span className="brand-mark">
              <img src="/up-crest.png" alt="" />
            </span>
            <span className="brand-text">
              <span className="brand-title">Insider Threat Detection</span>
              <span className="brand-sub">COS700 · University of Pretoria</span>
            </span>
          </NavLink>

          <button
            className="icon-button menu-button"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Menu"
            aria-expanded={menuOpen}
          >
            ☰
          </button>

          <nav className={menuOpen ? "nav open" : "nav"} aria-label="Main">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  isActive || (n.to === "/results" && RESULTS_PATHS.some((p) => pathname.startsWith(p)))
                    ? "nav-link active"
                    : "nav-link"
                }
              >
                {n.label}
              </NavLink>
            ))}
            <span className="nav-spacer" />
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className={pathname === "/" || pathname === "/models" ? "content wide" : "content"}>
        {/* Pages are lazy-loaded chunks: keep the header while one arrives. */}
        <Suspense fallback={<Loading />}>
          <Outlet context={{ experiments } satisfies LayoutContext} />
        </Suspense>
      </main>

      <footer className="footer">
        <div className="footer-inner">
          <span>
            <strong>A Hybrid Machine Learning Framework for Insider Threat Detection</strong> ·
            COS700 Research Project
          </span>
          <span>University of Pretoria · Department of Computer Science</span>
        </div>
      </footer>
    </div>
  );
}
