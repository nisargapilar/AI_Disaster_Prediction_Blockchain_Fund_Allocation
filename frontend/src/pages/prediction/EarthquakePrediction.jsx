import { useEffect, useState } from "react";
import { Mountain, RefreshCw, MapPin, Activity, BellRing } from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, SevBadge } from "../../components/ui";
import RealMap from "../../components/RealMap";
import Breadcrumb from "../../components/Breadcrumb";
import {
  fetchDetectedEarthquakes,
  fetchPredictedEarthquakes,
  normalizeDetection,
  normalizeAndDedupePredictions,
} from "../../api/earthquake";

export default function EarthquakePrediction() {
  const { theme } = useTheme();
  const s = surface(theme);
  const [predictions, setPredictions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [rawDetected, rawPredicted] = await Promise.all([
        fetchDetectedEarthquakes(),
        fetchPredictedEarthquakes(),
      ]);
      const detections = rawDetected.map(normalizeDetection);
      const preds = normalizeAndDedupePredictions(rawPredicted, detections);
      setPredictions(preds);
      if (preds.length && !selectedId) setSelectedId(preds[0].id);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const selected = predictions.find((p) => p.id === selectedId);
  const points = predictions
    .filter((p) => p.hasPosition)
    .map((p) => ({
      id: p.id,
      lat: p.rawLat,
      lon: p.rawLon,
      severity: p.severity,
    }));

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Prediction", "Earthquake"]} />
      <div className="p-5 max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mountain className={`w-5 h-5 ${accentText(theme, "violet")}`} />
            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Earthquake Prediction
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

        <div
          className={`rounded border border-dashed border-violet-400/30 bg-violet-400/5 text-[11px] font-mono px-4 py-2.5 ${accentText(theme, "violet")}`}
        >
          Prediction is forecast-only. It never moves fund_status — only
          detection does. Markers appear only for regions with a matching
          detected event on record.
        </div>

        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">
            Failed to reach backend: {error}. Check CORS and that the backend is
            running.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <Panel
              title="Risk Prediction Map"
              icon={MapPin}
              accent="violet"
              dashed
            >
              <RealMap
                points={points}
                selectedId={selectedId}
                onSelect={setSelectedId}
                mode="prediction"
              />
            </Panel>
          </div>

          <Panel title="Prediction Log" icon={BellRing} accent="violet" dashed>
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
              {loading && predictions.length === 0 && (
                <div className={`text-xs font-mono ${s.textMuted}`}>
                  Loading predictions…
                </div>
              )}
              {!loading && predictions.length === 0 && !error && (
                <div className={`text-xs font-mono ${s.textMuted}`}>
                  No predictions yet.
                </div>
              )}
              {predictions.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedId(p.id)}
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    p.id === selectedId
                      ? "border-violet-400/60 bg-violet-400/10"
                      : `${s.borderFaint} hover:border-violet-400/30`
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-mono ${s.textPrimary}`}>
                      {p.region}
                    </span>
                    <SevBadge severity={p.severity} />
                  </div>
                  <div className={`text-[10px] font-mono ${s.textMuted}`}>
                    {p.riskPct}% risk · {p.generated}
                  </div>
                </button>
              ))}
            </div>
          </Panel>
        </div>

        {selected && (
          <Panel
            title={`Prediction Detail — ${selected.id}`}
            icon={Activity}
            accent="violet"
            dashed
            right={<SevBadge severity={selected.severity} />}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
              <Field label="Region" value={selected.region} s={s} />
              <Field label="Risk Score" value={selected.riskScore} s={s} />
              <Field label="Risk %" value={`${selected.riskPct}%`} s={s} />
              <Field label="Generated" value={selected.generated} s={s} />
              <Field
                label="Sequence Length"
                value={selected.sequenceLength}
                s={s}
              />
              <Field
                label="Based On Events"
                value={selected.basedOnCount}
                s={s}
              />
              <Field
                label="Simulated"
                value={selected.isSimulated ? "Yes" : "No"}
                s={s}
              />
              <Field
                label="Map Position"
                value={selected.hasPosition ? "Matched" : "No match"}
                s={s}
              />
            </div>
            <div
              className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              About this model: risk scores come from a sequence model over
              recent detected events per region. This is a forecast, not a
              confirmed event — it triggers warnings, never fund release.
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
