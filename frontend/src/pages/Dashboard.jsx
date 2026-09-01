import { useEffect, useState } from "react";
import { ShieldCheck, BellRing, Activity, ArrowRight } from "lucide-react";
import { useTheme, surface, accentText } from "../theme/ThemeContext";
import { Panel, SevBadge, Badge } from "../components/ui";
import {
  fetchDetectedEarthquakes,
  normalizeDetection,
} from "../api/earthquake";

export default function Dashboard({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDetectedEarthquakes()
      .then((raw) => setEvents(raw.map(normalizeDetection)))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  const recent = [...events]
    .sort((a, b) => new Date(b.detected) - new Date(a.detected))
    .slice(0, 6);

  const stats = [
    { label: "Detected Events", value: events.length },
    {
      label: "Critical Severity",
      value: events.filter((e) => e.severity === "critical").length,
    },
    {
      label: "Funds Pending",
      value: events.filter((e) => e.fundStatus === "pending").length,
    },
    { label: "Modules Live", value: 4 },
  ];

  return (
    <div className="p-5 max-w-7xl mx-auto space-y-5">
      <div>
        <h1
          className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
        >
          Command Dashboard
        </h1>
        <p className={`text-xs font-mono ${s.textSecondary} mt-1`}>
          Detection confirms real events and can release funds. Prediction
          forecasts risk and sends warnings only.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stats.map((st) => (
          <div
            key={st.label}
            className={`rounded-md ${s.panel} border ${s.borderFaint} p-4`}
          >
            <div className={`text-2xl font-mono ${accentText(theme, "cyan")}`}>
              {loading ? "…" : st.value}
            </div>
            <div
              className={`text-[10px] uppercase tracking-widest font-mono ${s.textFaint} mt-1`}
            >
              {st.label}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button onClick={() => setView("detect-select")} className="text-left">
          <Panel
            title="Detection"
            icon={ShieldCheck}
            accent="cyan"
            right={
              <ArrowRight className={`w-4 h-4 ${accentText(theme, "cyan")}`} />
            }
          >
            <p className={`text-xs font-mono ${s.textSecondary}`}>
              Confirmed events from authoritative sources. Solid markers. Can
              trigger fund release.
            </p>
          </Panel>
        </button>

        <button onClick={() => setView("predict-select")} className="text-left">
          <Panel
            title="Prediction"
            icon={BellRing}
            accent="violet"
            dashed
            right={
              <ArrowRight
                className={`w-4 h-4 ${accentText(theme, "violet")}`}
              />
            }
          >
            <p className={`text-xs font-mono ${s.textSecondary}`}>
              Forecasted risk from model inference. Dashed markers. Sends
              warnings only, never moves funds.
            </p>
          </Panel>
        </button>
      </div>

      <Panel title="Recent Activity" icon={Activity} accent="cyan">
        <div className="space-y-2">
          {recent.length === 0 && (
            <div className={`text-xs font-mono ${s.textMuted}`}>
              {loading ? "Loading…" : "No recent detected events."}
            </div>
          )}
          {recent.map((e) => (
            <div
              key={e.id}
              className={`flex items-center justify-between p-3 rounded border ${s.borderFaint}`}
            >
              <div>
                <div className={`text-xs font-mono ${s.textPrimary}`}>
                  {e.name}
                </div>
                <div className={`text-[10px] font-mono ${s.textMuted}`}>
                  {e.detected}
                </div>
              </div>
              <SevBadge severity={e.severity} />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
