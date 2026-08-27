import { useState } from "react";
import { ThemeProvider, useTheme, surface } from "./theme/ThemeContext";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import DisasterSelect from "./pages/DisasterSelect";
import EarthquakeDetection from "./pages/detection/EarthquakeDetection";
import ForestFireDetection from "./pages/detection/ForestFireDetection";
import EarthquakePrediction from "./pages/prediction/EarthquakePrediction";
import ForestFirePrediction from "./pages/prediction/ForestFirePrediction";
import FundsPlaceholder from "./pages/funds/FundsPlaceholder";

function Shell() {
  const [view, setView] = useState("dashboard");
  const { theme } = useTheme();
  const s = surface(theme);

  let page;
  if (view === "dashboard") page = <Dashboard setView={setView} />;
  else if (view === "detect-select")
    page = <DisasterSelect mode="detection" setView={setView} />;
  else if (view === "predict-select")
    page = <DisasterSelect mode="prediction" setView={setView} />;
  else if (view === "eq-detection")
    page = <EarthquakeDetection setView={setView} />;
  else if (view === "forest-fire-detection")
  page = <ForestFireDetection setView={setView} />;
  else if (view === "eq-prediction")
    page = <EarthquakePrediction setView={setView} />;
  else if (view === "forest-fire-prediction")
  page = <ForestFirePrediction setView={setView} />;
  else if (view === "funds") page = <FundsPlaceholder />;
  else page = <Dashboard setView={setView} />;

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
      <Shell />
    </ThemeProvider>
  );
}
