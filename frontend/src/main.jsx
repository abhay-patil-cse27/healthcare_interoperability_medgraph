import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import VaidyaBot from "./components/ui/VaidyaBot";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
      <VaidyaBot />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#1e293b",
            color: "#f1f5f9",
            fontSize: "14px",
            borderRadius: "10px",
            padding: "12px 16px",
          },
          success: { iconTheme: { primary: "#10b981", secondary: "#f1f5f9" } },
          error:   { iconTheme: { primary: "#ef4444", secondary: "#f1f5f9" } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);

