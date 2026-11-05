import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { ThemeContext, type ThemePreference, type ThemeState } from "./context";

const STORAGE_KEY = "itd-theme";

/** Light unless the visitor chose dark on an earlier visit. */
function readStored(): ThemePreference {
  try {
    return localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setStoredPreference] = useState<ThemePreference>(readStored);

  // Apply the theme to <html> before React re-renders: charts read the CSS
  // colours while rendering, so they must already see the new theme's values.
  const setPreference = useCallback((p: ThemePreference) => {
    document.documentElement.dataset.theme = p;
    setStoredPreference(p);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = preference;
    try {
      localStorage.setItem(STORAGE_KEY, preference);
    } catch {
      // Storage unavailable (private mode): the choice lasts for this visit only.
    }
  }, [preference]);

  const value = useMemo<ThemeState>(
    () => ({ preference, resolved: preference, setPreference }),
    [preference, setPreference],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
