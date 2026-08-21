import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The build lands in the package's static directory, which FastAPI mounts at
// /ui — so `base` has to match or the asset URLs 404. The output is committed,
// which is what lets someone clone the repo and open the UI without npm.
export default defineConfig({
  plugins: [react()],
  base: "/ui/",
  build: {
    outDir: "../src/video_searching_agent/web/static",
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    // `npm run dev` talks to a locally running API.
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
