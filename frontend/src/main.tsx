import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./style.css";
async function start() {
  if (import.meta.env.VITE_NOTEPILOT_HOSTED === "1") {
    // This hostname is dedicated to NotePilot. Retire any earlier offline build.
    if ("serviceWorker" in navigator) {
      for (const registration of await navigator.serviceWorker.getRegistrations()) {
        await registration.unregister();
      }
    }
    if ("caches" in window) {
      await Promise.all((await caches.keys()).map((name) => caches.delete(name)));
    }
    indexedDB.deleteDatabase("notepilot-local");
  }
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}
void start();
