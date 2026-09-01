// vite.config.js — Vite build tool configuration
//
// Key configuration:
// - Proxy: In development, any request to /api/* from React
//   is automatically forwarded to http://localhost:5000/api/*
//   This avoids CORS issues during development.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,  // React dev server port

    // Proxy API calls to Flask during development
    // When React calls /api/health, Vite forwards it to http://localhost:5000/api/health
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // Environment variable prefix
  // Only variables starting with VITE_ are accessible in React code
  envPrefix: "VITE_",
});
