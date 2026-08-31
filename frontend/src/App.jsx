
import { useState } from "react";

import { ThemeProvider, useTheme, surface } from "./theme/ThemeContext";

import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import DisasterSelect from "./pages/DisasterSelect";

// Detection pages
import EarthquakeDetection from "./pages/detection/EarthquakeDetection";
import FloodDetection from "./pages/detection/FloodDetection";
import ForestFireDetection from "./pages/detection/ForestFireDetection";
import CycloneDetection from "./pages/detection/CycloneDetection";

// Prediction pages
import EarthquakePrediction from "./pages/prediction/EarthquakePrediction";
import FloodPrediction from "./pages/prediction/FloodPrediction";
import ForestFirePrediction from "./pages/prediction/ForestFirePrediction";
import CyclonePrediction from "./pages/prediction/CyclonePrediction";

// Funds
import FundsPlaceholder from "./pages/funds/FundsPlaceholder";

function Shell() {
  const [view, setView] = useState("dashboard");

  const { theme } = useTheme();
  const s = surface(theme);

  let page;

  // ============================================================
  // DASHBOARD
  // ============================================================
  if (view === "dashboard") {
    page = <Dashboard setView={setView} />;
  }

  // ============================================================
  // DETECTION SELECT
  // ============================================================
  else if (view === "detect-select") {
    page = (
      <DisasterSelect
        mode="detection"
        setView={setView}
      />
    );
  }

  // ============================================================
  // PREDICTION SELECT
  // ============================================================
  else if (view === "predict-select") {
    page = (
      <DisasterSelect
        mode="prediction"
        setView={setView}
      />
    );
  }

  // ============================================================
  // EARTHQUAKE DETECTION
  // ============================================================
  else if (view === "eq-detection") {
    page = <EarthquakeDetection setView={setView} />;
  }

  // ============================================================
  // FLOOD DETECTION
  // ============================================================
  else if (view === "flood-detection") {
    page = <FloodDetection setView={setView} />;
  }

  // ============================================================
  // FOREST FIRE DETECTION
  // ============================================================
  else if (view === "forest-fire-detection") {
    page = <ForestFireDetection setView={setView} />;
  }

  // ============================================================
  // CYCLONE DETECTION
  // ============================================================
  else if (view === "cyclone-detection") {
    page = <CycloneDetection setView={setView} />;
  }

  // ============================================================
  // EARTHQUAKE PREDICTION
  // ============================================================
  else if (view === "eq-prediction") {
    page = <EarthquakePrediction setView={setView} />;
  }

  // ============================================================
  // FLOOD PREDICTION
  // ============================================================
  else if (view === "flood-prediction") {
    page = <FloodPrediction setView={setView} />;
  }

  // ============================================================
  // FOREST FIRE PREDICTION
  // ============================================================
  else if (view === "forest-fire-prediction") {
    page = <ForestFirePrediction setView={setView} />;
  }

  // ============================================================
  // CYCLONE PREDICTION
  // ============================================================
  else if (view === "cyclone-prediction") {
    page = <CyclonePrediction setView={setView} />;
  }

  // ============================================================
  // FUNDS
  // ============================================================
  else if (view === "funds") {
    page = <FundsPlaceholder />;
  }

  // ============================================================
  // FALLBACK
  // ============================================================
  else {
    page = <Dashboard setView={setView} />;
  }

  return (
    <div className={`min-h-screen ${s.app}`}>
      <Navbar
        view={view}
        setView={setView}
      />

      {page}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <Shell />
    </ThemeProvider>
  );
}

