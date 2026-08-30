import { useEffect, useState } from "react";
import {
  Waves,
  RefreshCw,
  MapPin,
  Activity,
  Database,
} from "lucide-react";

import {
  useTheme,
  surface,
  accentText,
} from "../../theme/ThemeContext";

import {
  Panel,
  SevBadge,
} from "../../components/ui";

import RealMap from "../../components/RealMap";
import Breadcrumb from "../../components/Breadcrumb";

import {
  fetchDetectedFloods,
  normalizeFloodDetection,
} from "../../api/flood";

export default function FloodDetection({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const raw = await fetchDetectedFloods();

      console.log("FLOOD API RESPONSE:", raw);

      const norm = Array.isArray(raw)
        ? raw.map(normalizeFloodDetection)
        : [];

      console.log("NORMALIZED FLOOD EVENTS:", norm);

      setEvents(norm);

      if (
        norm.length > 0 &&
        !selectedId
      ) {
        setSelectedId(norm[0].id);
      }
    } catch (e) {
      console.error(
        "Flood detection error:",
        e
      );

      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const selected = events.find(
    (e) => e.id === selectedId
  );

  // ==========================================================
  // FLOOD MAP POINTS
  // ==========================================================

  const points = events
    .filter(
      (e) =>
        Number.isFinite(e.rawLat) &&
        Number.isFinite(e.rawLon)
    )
    .map((e) => ({
      id: e.id,
      name: e.name,
      region: e.region,
      lat: e.rawLat,
      lon: e.rawLon,
      severity: e.severity,
    }));

  return (
    <div>
      <Breadcrumb
        trail={[
          "Dashboard",
          "Detection",
          "Flood",
        ]}
      />

      <div className="p-5 max-w-7xl mx-auto space-y-4">

        {/* ==================================================
            HEADER
        ================================================== */}

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-2">

            <Waves
              className={`w-5 h-5 ${accentText(
                theme,
                "cyan"
              )}`}
            />

            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Flood Detection
            </h1>

          </div>

          <button
            onClick={load}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono uppercase tracking-widest border ${s.borderSoft} ${s.tint} hover:${s.tintStrong} ${s.textSecondary}`}
          >

            <RefreshCw
              className={`w-3.5 h-3.5 ${
                loading
                  ? "animate-spin"
                  : ""
              }`}
            />

            Refresh

          </button>

        </div>

        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">
            Failed to reach flood backend:{" "}
            {error}
          </div>
        )}

        {/* ==================================================
            MAP + EVENT LOG
        ================================================== */}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* MAP */}

          <div className="lg:col-span-2">

            <Panel
              title="Live Flood Detection Map"
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

          {/* EVENT LOG */}

          <Panel
            title="Flood Event Log"
            icon={Database}
            accent="cyan"
          >

            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">

              {loading &&
                events.length === 0 && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    Loading flood events…
                  </div>
                )}

              {!loading &&
                events.length === 0 &&
                !error && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    No detected flood events yet.
                  </div>
                )}

              {events.map((e) => (
                <button
                  key={e.id}
                  onClick={() =>
                    setSelectedId(e.id)
                  }
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    e.id === selectedId
                      ? "border-cyan-400/60 bg-cyan-400/10"
                      : `${s.borderFaint} hover:border-cyan-400/30`
                  }`}
                >

                  <div className="flex items-center justify-between mb-1">

                    <span
                      className={`text-xs font-mono ${s.textPrimary}`}
                    >
                      {e.name}
                    </span>

                    <SevBadge
                      severity={e.severity}
                    />

                  </div>

                  <div
                    className={`text-[10px] font-mono ${s.textMuted}`}
                  >
                    {e.detected}
                  </div>

                </button>
              ))}

            </div>

          </Panel>

        </div>

        {/* ==================================================
            FLOOD EVENT DETAILS
        ================================================== */}

        {selected && (
          <Panel
            title={`Flood Event Detail — ${selected.id}`}
            icon={Activity}
            accent="cyan"
            right={
              <SevBadge
                severity={selected.severity}
              />
            }
          >

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">

              <Field
                label="Region"
                value={selected.region}
                s={s}
              />

              <Field
                label="Rainfall"
                value={selected.rainfall}
                s={s}
              />

              <Field
                label="River Level"
                value={selected.riverLevel}
                s={s}
              />

              <Field
                label="Humidity"
                value={selected.humidity}
                s={s}
              />

              <Field
                label="Temperature"
                value={selected.temperature}
                s={s}
              />

              <Field
                label="Probability"
                value={
                  selected.probability != null
                    ? `${Math.round(
                        Number(
                          selected.probability
                        ) * 100
                      )}%`
                    : "—"
                }
                s={s}
              />

              <Field
                label="Risk Score"
                value={selected.riskScore}
                s={s}
              />

              <Field
                label="Risk %"
                value={
                  selected.riskPct != null
                    ? `${selected.riskPct}%`
                    : "—"
                }
                s={s}
              />

              <Field
                label="Fund Status"
                value={selected.fundStatus}
                s={s}
              />

              <Field
                label="Source"
                value={selected.source}
                s={s}
              />

              <Field
                label="Coordinates"
                value={selected.coords}
                s={s}
              />

              <Field
                label="Detected At"
                value={selected.detected}
                s={s}
              />

            </div>

            <div
              className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              Flood detection data is loaded
              directly from the connected FastAPI
              backend. Values shown here come
              directly from the API response.
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