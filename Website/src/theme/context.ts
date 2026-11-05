import { createContext, useContext } from "react";

/** The site opens in light mode; the toggle switches to dark and back. The
 * resolved value is what is on screen, which charts need because they read
 * their colours from CSS. */
export type ThemePreference = "light" | "dark";
export type ResolvedTheme = ThemePreference;

export interface ThemeState {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  setPreference: (p: ThemePreference) => void;
}

export const ThemeContext = createContext<ThemeState | null>(null);

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used inside <ThemeProvider>");
  return ctx;
}
