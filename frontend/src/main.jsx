// main.jsx — React application entry point
// This is the very first JavaScript file that runs in the browser.
// It mounts the React app into the <div id="root"> in index.html.

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// StrictMode helps catch common bugs during development.
// It runs component lifecycle methods twice in development only.
// No performance impact in production.
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
