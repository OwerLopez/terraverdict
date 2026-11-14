/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "var(--page)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        "surface-3": "var(--surface-3)",
        line: "var(--border)",
        "line-strong": "var(--border-strong)",
        ink: { DEFAULT: "var(--ink)", 2: "var(--ink-2)", 3: "var(--ink-3)" },
        accent: { DEFAULT: "var(--accent)", soft: "var(--accent-soft)", ink: "var(--accent-ink)" },
        good: "var(--good)",
        warning: "var(--warning)",
        serious: "var(--serious)",
        critical: "var(--critical)",
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", '"Segoe UI"', "Roboto", "sans-serif"],
        mono: ['ui-monospace', '"SF Mono"', "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        tarjeta: "0 1px 2px rgba(0,0,0,0.04), 0 1px 1px rgba(0,0,0,0.02)",
        flotante: "0 12px 32px -12px rgba(0,0,0,0.35), 0 2px 6px rgba(0,0,0,0.08)",
      },
      keyframes: {
        aparecer: { from: { opacity: "0", transform: "translateY(4px)" }, to: { opacity: "1", transform: "none" } },
        pulso: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.35" } },
      },
      animation: {
        aparecer: "aparecer 240ms ease-out both",
        pulso: "pulso 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
