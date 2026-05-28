"""
Configuration for TailwindCSS 4.0 with FastAPI

This config works with Vite 7 for asset bundling.
"""

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./resources/**/*.{html,js}",
    "./templates/**/*.{html,js}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c2d6b",
        },
        secondary: {
          50: "#f8fafc",
          100: "#f1f5f9",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          900: "#0f172a",
        },
        success: {
          50: "#f0fdf4",
          500: "#22c55e",
          600: "#16a34a",
          900: "#14532d",
        },
        danger: {
          50: "#fef2f2",
          500: "#ef4444",
          600: "#dc2626",
          900: "#7f1d1d",
        },
        warning: {
          50: "#fffbeb",
          500: "#f59e0b",
          600: "#d97706",
          900: "#78350f",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["Fira Code", "monospace"],
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        md: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
        lg: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
        xl: "0 20px 25px -5px rgb(0 0 0 / 0.1)",
      },
    },
  },
  plugins: [
    // Forms plugin para mejor styling de inputs
    require("@tailwindcss/forms"),
  ],
};
