import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      disable: process.env.VITE_NOTEPILOT_HOSTED === "1",
      registerType: "prompt",
      includeAssets: ["icon.svg"],
      manifest: {
        name: "NotePilot · Dein Musikpartner",
        short_name: "NotePilot",
        description: "Noten erkennen und lokal üben",
        theme_color: "#165e51",
        background_color: "#f6f8f5",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2,sf2,txt}"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [{ urlPattern: /\/api\/v1\/.*$/, handler: "NetworkOnly" }],
      },
    }),
  ],
  server: { host: "127.0.0.1", proxy: { "/api": "http://127.0.0.1:8000" } },
  build: { chunkSizeWarningLimit: 2000 },
});
