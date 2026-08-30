
import { Mountain, Wind, Waves, Flame } from "lucide-react";
import { useTheme, surface, accentText } from "../theme/ThemeContext";
import { Badge } from "../components/ui";

const DISASTERS = [
  {
    id: "earthquake",
    label: "Earthquake",
    icon: Mountain,
    active: true,
  },
  {
    id: "cyclone",
    label: "Cyclone",
    icon: Wind,
    active: false,
  },
  {
    id: "flood",
    label: "Flood",
    icon: Waves,
    active: true,
  },
  {
    id: "forest_fire",
    label: "Forest Fire",
    icon: Flame,
    active: true,
  },
];

export default function DisasterSelect({ mode, setView }) {
  const { theme } = useTheme();
  const s = surface(theme);

  const accent = mode === "detection" ? "cyan" : "violet";

  const goto = (disasterId) => {
    // =========================
    // EARTHQUAKE
    // =========================
    if (disasterId === "earthquake") {
      setView(
        mode === "detection"
          ? "eq-detection"
          : "eq-prediction"
      );
      return;
    }

    // =========================
    // FLOOD
    // =========================
    if (disasterId === "flood") {
      setView(
        mode === "detection"
          ? "flood-detection"
          : "flood-prediction"
      );
      return;
    }

    // =========================
    // FOREST FIRE
    // =========================
    if (disasterId === "forest_fire") {
      setView(
        mode === "detection"
          ? "forest-fire-detection"
          : "forest-fire-prediction"
      );
      return;
    }
  };

  return (
    <div className="p-5 max-w-4xl mx-auto">
      {/* HEADER */}
      <div
        className={`text-xs font-mono uppercase tracking-widest mb-1 ${accentText(
          theme,
          accent
        )}`}
      >
        {mode === "detection"
          ? "Detection // Select Disaster Module"
          : "Prediction // Select Disaster Module"}
      </div>

      <div className={`text-sm mb-6 ${s.textSecondary}`}>
        {mode === "detection"
          ? "Confirmed real events per module. Selecting a module opens its live detection map."
          : "Early-warning forecasts per module. Selecting a module opens its risk-prediction map."}
      </div>

      {/* DISASTER CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {DISASTERS.map((d) => {
          const Icon = d.icon;

          return (
            <button
              key={d.id}
              disabled={!d.active}
              onClick={() => goto(d.id)}
              className={`rounded-md p-5 flex flex-col items-center gap-3 border transition-colors ${
                d.active
                  ? `${s.panel} ${
                      accent === "cyan"
                        ? "border-cyan-400/30 hover:border-cyan-400/60 hover:bg-cyan-400/5"
                        : "border-violet-400/30 hover:border-violet-400/60 hover:bg-violet-400/5"
                    } cursor-pointer`
                  : `${s.panel} ${s.borderFaint} opacity-40 cursor-not-allowed`
              }`}
            >
              {/* ICON */}
              <Icon
                className={`w-7 h-7 ${
                  d.active
                    ? accentText(theme, accent)
                    : s.textFaint
                }`}
              />

              {/* NAME */}
              <span
                className={`text-sm font-mono uppercase tracking-widest ${s.textBody}`}
              >
                {d.label}
              </span>

              {/* STATUS */}
              <Badge
                className={
                  d.active
                    ? accent === "cyan"
                      ? "bg-cyan-400/10 text-cyan-600 border border-cyan-400/30"
                      : "bg-violet-400/10 text-violet-600 border border-violet-400/30"
                    : `${s.tint} ${s.textFaint} border ${s.borderSoft}`
                }
              >
                {d.active ? "Live" : "Coming soon"}
              </Badge>
            </button>
          );
        })}
      </div>
    </div>
  );
}

