/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        page: "#0b0d12",
        surface: "#12151c",
        "surface-2": "#171b23",
        chart: "#14171f",
        border: "rgba(255,255,255,0.08)",
        ink: {
          primary: "#ffffff",
          secondary: "#a7abb8",
          muted: "#6b7280",
        },
        accent: {
          DEFAULT: "#3987e5",
          dim: "#1c5cab",
        },
        status: {
          good: "#0ca30c",
          warning: "#fab219",
          serious: "#ec835a",
          critical: "#d03b3b",
        },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
