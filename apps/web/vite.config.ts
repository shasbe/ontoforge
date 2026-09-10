import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",            // relative base so the built site works from any path
  server: { port: 5173 },
});
