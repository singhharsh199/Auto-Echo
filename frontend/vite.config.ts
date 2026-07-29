import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The UI is authored in vanilla CSS (src/index.css); no CSS framework is used,
// so no Tailwind plugin is registered here.
export default defineConfig({
  plugins: [react()],
});
