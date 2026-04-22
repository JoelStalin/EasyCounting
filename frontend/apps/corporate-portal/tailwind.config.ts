import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "#cbd5e1",
        input: "#cbd5e1",
        background: "#f8fafc",
        foreground: "#0f172a",
        sand: "#f8f5ef",
        ink: "#0f172a",
        accent: "#0f766e",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
