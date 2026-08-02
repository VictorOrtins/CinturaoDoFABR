import { useTheme } from "../theme/theme-context";
import "./ThemeToggle.css";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
      title={isDark ? "Modo claro" : "Modo escuro"}
    >
      {isDark ? (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
          <path d="M12 4.5a1 1 0 0 1-1-1V2a1 1 0 1 1 2 0v1.5a1 1 0 0 1-1 1Zm0 15a1 1 0 0 1 1 1V22a1 1 0 1 1-2 0v-1.5a1 1 0 0 1 1-1ZM4.5 12a1 1 0 0 1-1 1H2a1 1 0 1 1 0-2h1.5a1 1 0 0 1 1 1Zm17.5 0a1 1 0 0 1-1 1h-1.5a1 1 0 1 1 0-2H21a1 1 0 0 1 1 1ZM6.34 6.34a1 1 0 0 1-1.42 0L3.87 5.29a1 1 0 0 1 1.42-1.42l1.05 1.05a1 1 0 0 1 0 1.42Zm12.02 12.02a1 1 0 0 1-1.41 0l-1.05-1.05a1 1 0 0 1 1.41-1.41l1.05 1.05a1 1 0 0 1 0 1.41ZM19.71 5.29a1 1 0 0 1 0 1.42l-1.05 1.05a1 1 0 1 1-1.41-1.42l1.05-1.05a1 1 0 0 1 1.41 0ZM7.75 18.36a1 1 0 0 1 0 1.41l-1.05 1.05a1 1 0 1 1-1.42-1.41l1.05-1.05a1 1 0 0 1 1.42 0ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Z" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
          <path d="M20.7 14.9a8.6 8.6 0 0 1-10.6-10.6 1 1 0 0 0-1.3-1.2A10.6 10.6 0 1 0 21.9 16.2a1 1 0 0 0-1.2-1.3Z" />
        </svg>
      )}
    </button>
  );
}
