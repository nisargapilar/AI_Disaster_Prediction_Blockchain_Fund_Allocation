import { useEffect, useState } from "react";
import {
  Flame,
  RefreshCw,
  MapPin,
  Activity,
  Database,
} from "lucide-react";

import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, SevBadge } from "../../components/ui";
import RealMap from "../../components/RealMap";
import Breadcrumb from "../../components/Breadcrumb";
import { fetchForestFireEvents } from "../../api/forestFire";

export default function ForestFireDetection({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadEvents() {
    setLoading(true);
    setError(null);

    try {
      const raw = await fetchForestFireEvents();

      setEvents(raw);

      if (raw.length && !selectedId) {
        setSelectedId(raw[0].event_id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEvents();

    // Auto-refresh every 30 seconds, matching backend polling cadence
    const interval = setInterval(loadEvents, 30000);
    return () => clearInterval(interval);
  }, []);

  const selected = events.find(
    (e) => e.event_id === selectedId
  );

  const points = events
    .filter(
      (e) =>
        e.location &&
        Number.isFinite(Number(e.location.lat)) &&
        Number.isFinite(Number(e.location.lon))
    )
    .map((e) => ({
      id: e.event_id,
      lat: Number(e.location.lat),
      lon: Number(e.location.lon),
      severity: e.severity_tier || "low",
    }));

  return (
    <div>
      <Breadcrumb
        trail={["Dashboard", "Detection", "Forest Fire"]}
      />

      <div className="p-5 max-w-7xl mx-auto space-y-4">

        {/* HEADER */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame
              className={`w-5 h-5 ${accentText(
                theme,
                "cyan"
              )}`}
            />

            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Forest Fire Detection
            </h1>
          </div>

          <button
            onClick={loadEvents}
            disabled={loading}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono uppercase tracking-widest border ${s.borderSoft} ${s.tint} ${s.textSecondary}`}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${
                loading ? "animate-spin" : ""
              }`}
            />

            Refresh
          </button>
        </div>

        {/* ERROR */}
        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">
            Failed to reach Forest Fire backend: {error}
            <br />
            Make sure FastAPI is running on
            http://127.0.0.1:8000
          </div>
        )}

        {/* MAP + EVENTS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          <div className="lg:col-span-2">
            <Panel
              title="Live Forest Fire Detection Map"
              icon={MapPin}
              accent="cyan"
            >
              <RealMap
                points={points}
                selectedId={selectedId}
                onSelect={setSelectedId}
                mode="detection"
              />
            </Panel>
          </div>

          <Panel
            title="Forest Fire Event Log"
            icon={Database}
            accent="cyan"
          >
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">

              {loading && events.length === 0 && (
                <div
                  className={`text-xs font-mono ${s.textMuted}`}
                >
                  Loading events...
                </div>
              )}

              {!loading &&
                events.length === 0 &&
                !error && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    No forest fire events found.
                  </div>
                )}

              {events.map((e) => (
                <button
                  key={e.event_id}
                  onClick={() =>
                    setSelectedId(e.event_id)
                  }
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    e.event_id === selectedId
                      ? "border-cyan-400/60 bg-cyan-400/10"
                      : `${s.borderFaint} hover:border-cyan-400/30`
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">

                    <span
                      className={`text-xs font-mono ${s.textPrimary}`}
                    >
                      {e.location?.region ||
                        "Forest Fire Event"}
                    </span>

                    <SevBadge
                      severity={
                        e.severity_tier || "low"
                      }
                    />
                  </div>

                  <div
                    className={`text-[10px] font-mono ${s.textMuted}`}
                  >
                    {e.source || "NASA FIRMS"}
                  </div>
                </button>
              ))}
            </div>
          </Panel>
        </div>

        {/* EVENT DETAIL */}
        {selected && (
          <Panel
            title={`Event Detail — ${selected.event_id}`}
            icon={Activity}
            accent="cyan"
            right={
              <SevBadge
                severity={
                  selected.severity_tier || "low"
                }
              />
            }
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">

              <Field
                label="Severity"
                value={selected.severity_tier}
                s={s}
              />

              <Field
                label="Risk Score"
                value={selected.risk_score}
                s={s}
              />

              <Field
                label="Fund Status"
                value={selected.fund_status}
                s={s}
              />

              <Field
                label="Source"
                value={selected.source}
                s={s}
              />

              <Field
                label="Region"
                value={selected.location?.region}
                s={s}
              />

              <Field
                label="Latitude"
                value={selected.location?.lat}
                s={s}
              />

              <Field
                label="Longitude"
                value={selected.location?.lon}
                s={s}
              />

              <Field
                label="Detected At"
                value={selected.event_time}
                s={s}
              />

              <Field
                label="FRP"
                value={selected.input_data?.frp}
                s={s}
              />

              <Field
                label="Brightness"
                value={selected.input_data?.brightness}
                s={s}
              />

              <Field
                label="ML Confidence"
                value={
                  selected.input_data?.ml_confidence
                }
                s={s}
              />

              <Field
                label="ML Prediction"
                value={
                  selected.input_data?.ml_prediction
                }
                s={s}
              />

            </div>

            {selected.input_data
              ?.ml_probabilities && (
              <div
                className={`mt-4 pt-4 border-t ${s.borderFaint}`}
              >
                <div
                  className={`text-[9px] uppercase tracking-widest ${s.textFaint} mb-2`}
                >
                  XGBoost Probabilities
                </div>

                <div className="grid grid-cols-3 gap-3 text-xs font-mono">

                  <Probability
                    label="Low"
                    value={
                      selected.input_data
                        .ml_probabilities.low
                    }
                    s={s}
                  />

                  <Probability
                    label="Medium"
                    value={
                      selected.input_data
                        .ml_probabilities.medium
                    }
                    s={s}
                  />

                  <Probability
                    label="High"
                    value={
                      selected.input_data
                        .ml_probabilities.high
                    }
                    s={s}
                  />

                </div>
              </div>
            )}

            <div
              className={`mt-4 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              Source feed: NASA FIRMS. Detection uses the
              Forest Fire XGBoost model and stores the resulting
              severity and ML probabilities.
            </div>

          </Panel>
        )}

      </div>
    </div>
  );
}

function Field({ label, value, s }) {
  return (
    <div>
      <div
        className={`text-[9px] uppercase tracking-widest ${s.textFaint} mb-1`}
      >
        {label}
      </div>

      <div className={s.textBody}>
        {value ?? "—"}
      </div>
    </div>
  );
}

function Probability({ label, value, s }) {
  const percentage =
    typeof value === "number"
      ? `${(value * 100).toFixed(1)}%`
      : value ?? "—";

  return (
    <div
      className={`rounded border ${s.borderFaint} p-3`}
    >
      <div
        className={`text-[9px] uppercase tracking-widest ${s.textFaint}`}
      >
        {label}
      </div>

      <div className={`mt-1 ${s.textBody}`}>
        {percentage}
      </div>
    </div>
  );
}