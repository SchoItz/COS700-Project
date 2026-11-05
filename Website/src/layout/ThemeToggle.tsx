import { useTheme } from "../theme/context";

/** Switches between light (the default) and dark mode. */
export default function ThemeToggle() {
  const { preference, setPreference } = useTheme();
  const dark = preference === "dark";
  return (
    <button
      className="icon-button"
      onClick={() => setPreference(dark ? "light" : "dark")}
      aria-pressed={dark}
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? "☀ Light mode" : "☾ Dark mode"}
    </button>
  );
}
