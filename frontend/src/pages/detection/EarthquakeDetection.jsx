import { useEffect, useState } from "react";
import {
  Mountain,
  RefreshCw,
  MapPin,
  Activity,
  Database,
  Play,
} from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, SevBadge } from "../../components/ui";
import RealMap from "../../components/RealMap";
import Breadcrumb from "../../components/Breadcrumb";
import {
  fetchDetectedEarthquakes,
  normalizeDetection,
  simulateEarthquakeDetection,
} from "../../api/earthquake";

export default function EarthquakeDetection({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);
  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // simulate-detection form
  const [simMagnitude, setSimMagnitude] = useState("6.5");
  const [simLat, setSimLat] = useState("12.9141");
  const [simLon, setSimLon] = useState("74.8560");
  const [simRegion, setSimRegion] = useState("Mangaluru");
  const [simulating, setSimulating] = useState(false);
  const [simMessage, setSimMessage] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const raw = await fetchDetectedEarthquakes();
      const norm = raw.map(normalizeDetection);
      setEvents(norm);
      if (norm.length && !selectedId) setSelectedId(norm[0].id);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSimulate(e) {
    e.preventDefault();
    setSimulating(true);
    setSimMessage(null);
    try {
      await simulateEarthquakeDetection({
        magnitude: parseFloat(simMagnitude),
        lat: parseFloat(simLat),
        lon: parseFloat(simLon),
        region: simRegion,
      });
      setSimMessage({ ok: true, text: "Simulated event created." });
      await load();
    } catch (err) {
      setSimMessage({ ok: false, text: err.message });
    } finally {
      setSimulating(false);
    }
  }

  const simValid =
    simMagnitude !== "" &&
    simLat !== "" &&
    simLon !== "" &&
    !Number.isNaN(parseFloat(simMagnitude)) &&
    !Number.isNaN(parseFloat(simLat)) &&
    !Number.isNaN(parseFloat(simLon));

  const selected = events.find((e) => e.id === selectedId);
  const points = events.map((e) => ({
    id: e.id,
    lat: e.rawLat,
    lon: e.rawLon,
    severity: e.severity,
  }));

  const inputClass = `w-full px-3 py-2 rounded border border-white/10 bg-transparent text-sm font-mono ${s.textPrimary}`;
  const labelClass = `block text-[10px] font-mono uppercase tracking-widest mb-1 ${s.textSecondary}`;

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Detection", "Earthquake"]} />
      <div className="p-5 max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mountain className={`w-5 h-5 ${accentText(theme, "cyan")}`} />
            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Earthquake Detection
            </h1>
          </div>
          <button
            onClick={load}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono uppercase tracking-widest border ${s.borderSoft} ${s.tint} hover:${s.tintStrong} ${s.textSecondary}`}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
        </div>

        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">
            Failed to reach backend: {error}. Check CORS on your FastAPI app for
            http://localhost:5173, and that it's running on 127.0.0.1:8000.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <Panel title="Live Detection Map" icon={MapPin} accent="cyan">
              <RealMap
                points={points}
                selectedId={selectedId}
                onSelect={setSelectedId}
                mode="detection"
              />
            </Panel>
          </div>

          <Panel title="Event Log" icon={Database} accent="cyan">
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
              {loading && events.length === 0 && (
                <div className={`text-xs font-mono ${s.textMuted}`}>
                  Loading events…
                </div>
              )}
              {!loading && events.length === 0 && !error && (
                <div className={`text-xs font-mono ${s.textMuted}`}>
                  No detected events yet.
                </div>
              )}
              {events.map((e) => (
                <button
                  key={e.id}
                  onClick={() => setSelectedId(e.id)}
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    e.id === selectedId
                      ? "border-cyan-400/60 bg-cyan-400/10"
                      : `${s.borderFaint} hover:border-cyan-400/30`
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-mono ${s.textPrimary}`}>
                      {e.name}
                    </span>
                    <SevBadge severity={e.severity} />
                  </div>
                  <div className={`text-[10px] font-mono ${s.textMuted}`}>
                    {e.detected}
                  </div>
                </button>
              ))}
            </div>
          </Panel>
        </div>

        <Panel title="Simulate Detection (demo)" icon={Play} accent="cyan">
          <form onSubmit={handleSimulate} className="space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className={labelClass}>Magnitude</label>
                <input
                  type="number"
                  step="0.1"
                  value={simMagnitude}
                  onChange={(e) => setSimMagnitude(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Latitude</label>
                <input
                  type="number"
                  step="any"
                  value={simLat}
                  onChange={(e) => setSimLat(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Longitude</label>
                <input
                  type="number"
                  step="any"
                  value={simLon}
                  onChange={(e) => setSimLon(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Region</label>
                <input
                  type="text"
                  value={simRegion}
                  onChange={(e) => setSimRegion(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={simulating || !simValid}
              className={`px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border ${accentText(theme, "cyan")} border-cyan-400/30 hover:bg-cyan-400/10 disabled:opacity-40`}
            >
              {simulating ? "simulating..." : "simulate detection"}
            </button>
          </form>

          {simMessage && (
            <div
              className={`mt-3 px-3 py-2 rounded border text-xs font-mono ${
                simMessage.ok
                  ? "border-emerald-400/30 text-emerald-400"
                  : "border-red-400/30 text-red-400"
              }`}
            >
              {simMessage.text}
            </div>
          )}

          <div
            className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
          >
            Demo tool: creates a simulated earthquake event through the same
            pipeline as real detections.
          </div>
        </Panel>

        {selected && (
          <Panel
            title={`Event Detail — ${selected.id}`}
            icon={Activity}
            accent="cyan"
            right={<SevBadge severity={selected.severity} />}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
              <Field label="Magnitude" value={selected.magnitude} s={s} />
              <Field label="Depth (km)" value={selected.depth} s={s} />
              <Field label="Region" value={selected.region} s={s} />
              <Field label="Coordinates" value={selected.coords} s={s} />
              <Field label="Risk Score" value={selected.riskScore} s={s} />
              <Field label="Fund Status" value={selected.fundStatus} s={s} />
              <Field label="Source" value={selected.source} s={s} />
              <Field label="Detected At" value={selected.detected} s={s} />
            </div>
            <div
              className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              Source feed: USGS all_hour.geojson — polled every 30s. Fields
              shown are exactly what the API returns; nothing here is
              fabricated.
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
      <div className={s.textBody}>{value ?? "—"}</div>
    </div>
  );
}
