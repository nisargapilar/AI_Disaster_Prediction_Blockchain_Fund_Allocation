import { useState } from "react";

import { ThemeProvider, useTheme, surface } from "./theme/ThemeContext";
import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/useAuth";

import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import DisasterSelect from "./pages/DisasterSelect";
import Login from "./pages/Login";

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

// Alerts
import Subscribe from "./pages/Subscribe.jsx";

// Funds
import FundsPlaceholder from "./pages/funds/FundsPlaceholder";
import BeneficiaryCard from "./pages/funds/BeneficiaryCard";
import VerifyBeneficiary from "./pages/funds/VerifyBeneficiary";
import VerifiedBeneficiaries from "./pages/funds/VerifiedBeneficiaries";

function Shell() {
  const [view, setView] = useState("dashboard");

  const { theme } = useTheme();
  const s = surface(theme);
  const { operator, loading } = useAuth();

  let page;

  if (view === "dashboard") {
    page = <Dashboard setView={setView} />;
  } else if (view === "detect-select") {
    page = <DisasterSelect mode="detection" setView={setView} />;
  } else if (view === "predict-select") {
    page = <DisasterSelect mode="prediction" setView={setView} />;
  } else if (view === "eq-detection") {
    page = <EarthquakeDetection setView={setView} />;
  } else if (view === "flood-detection") {
    page = <FloodDetection setView={setView} />;
  } else if (view === "forest-fire-detection") {
    page = <ForestFireDetection setView={setView} />;
  } else if (view === "cyclone-detection") {
    page = <CycloneDetection setView={setView} />;
  } else if (view === "eq-prediction") {
    page = <EarthquakePrediction setView={setView} />;
  } else if (view === "flood-prediction") {
    page = <FloodPrediction setView={setView} />;
  } else if (view === "forest-fire-prediction") {
    page = <ForestFirePrediction setView={setView} />;
  } else if (view === "cyclone-prediction") {
    page = <CyclonePrediction setView={setView} />;
  } else if (view === "subscribe") {
    page = <Subscribe />;
  } else if (view === "login") {
    page = <Login setView={setView} />;
  } else if (view === "verify-beneficiary") {
    // Protected: only logged-in operators can reach the verify form
    if (loading) {
      page = (
        <div className={`p-5 text-sm font-mono ${s.textSecondary}`}>
          checking session...
        </div>
      );
    } else if (!operator) {
      page = <Login setView={setView} />;
    } else {
      page = <VerifyBeneficiary />;
    }
  } else if (view === "beneficiary-card") {
    page = <BeneficiaryCard setView={setView} />;
  } else if (view === "verified-list") {
    page = <VerifiedBeneficiaries />;
  } else if (view === "funds") {
    page = <FundsPlaceholder setView={setView} />;
  } else {
    page = <Dashboard setView={setView} />;
  }

  return (
    <div className={`min-h-screen ${s.app}`}>
      <Navbar view={view} setView={setView} />

      {page}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </ThemeProvider>
  );
}
