import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("lucide-react")) {
              return "icons";
            }
            if (id.includes("@tanstack") || id.includes("axios") || id.includes("zustand")) {
              return "data";
            }
            if (id.includes("react-router") || id.includes("@remix-run")) {
              return "router";
            }
            if (
              id.includes("react-dom") ||
              id.includes("scheduler") ||
              id.includes("react-joyride") ||
              id.includes("@gilbarbara") ||
              id.match(/[\\/]node_modules[\\/ ]react[\\/]/)
            ) {
              return "react-core";
            }
          }

          if (id.includes("/packages/ui/src/") || id.includes("\\packages\\ui\\src\\")) {
            return "ui";
          }

          if (id.includes("/packages/api-client/src/") || id.includes("\\packages\\api-client\\src\\")) {
            return "api-client";
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    host: "0.0.0.0",
  },
});
