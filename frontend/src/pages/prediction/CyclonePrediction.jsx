
import { useEffect, useState } from "react";
import {
  Wind,
  RefreshCw,
  MapPin,
  Activity,
  BellRing,
} from "lucide-react";

import {
  useTheme,
  surface,
  accentText,
} from "../../theme/ThemeContext";

import { Panel, SevBadge } from "../../components/ui";
import RealMap from "../../components/RealMap";
import Breadcrumb from "../../components/Breadcrumb";

const API_URL = "http://127.0.0.1:8000";

export default function CyclonePrediction() {
  const { theme } = useTheme();
  const s = surface(theme);

  const [predictions, setPredictions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ============================================================
  // LOAD CYCLONE PREDICTIONS
  // ============================================================

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cyclone/predicted-cyclone-events`
      );

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const rawPredictions = await response.json();

      // ========================================================
      // KEEP ONLY THE LATEST PREDICTION FOR EACH REGION
      // ========================================================

      const latestByRegion = new Map();

      for (const prediction of rawPredictions) {
        const existing = latestByRegion.get(
          prediction.region
        );

        if (
          !existing ||
          new Date(prediction.predicted_time) >
            new Date(existing.predicted_time)
        ) {
          latestByRegion.set(
            prediction.region,
            prediction
          );
        }
      }

      // ========================================================
      // CONVERT BACKEND DATA INTO UI DATA
      // ========================================================

      const normalized = Array.from(
        latestByRegion.values()
      )
        .sort(
          (a, b) =>
            new Date(b.predicted_time) -
            new Date(a.predicted_time)
        )
        .map((prediction) => {
          const features =
            prediction.input_data?.features || {};

          return {
            id: prediction.prediction_id,

            region: prediction.region,

            riskScore:
              prediction.risk_score ?? 0,

            riskPct: Math.round(
              (prediction.risk_score ?? 0) * 100
            ),

            severity:
              prediction.severity_tier || "low",

            generated:
              formatTime(
                prediction.predicted_time
              ),

            predictedTime:
              prediction.predicted_time,

            probability:
              prediction.input_data
                ?.prediction_probability ?? 0,

            intensification:
              prediction.input_data
                ?.predicted_intensification ?? false,

            lat:
              typeof features.LAT === "number"
                ? features.LAT
                : null,

            lon:
              typeof features.LON === "number"
                ? features.LON
                : null,

            wind:
              features.WMO_WIND ?? null,

            pressure:
              features.WMO_PRES ?? null,

            stormDirection:
              features.STORM_DIR ?? null,

            stormSpeed:
              features.STORM_SPEED ?? null,

            distanceToLand:
              features.DIST2LAND ?? null,

            windChange:
              features.wind_change ?? null,

            previousWind:
              features.previous_wind ?? null,
          };
        });

      setPredictions(normalized);

      if (
        normalized.length > 0 &&
        !selectedId
      ) {
        setSelectedId(normalized[0].id);
      }
    } catch (e) {
      console.error(
        "Cyclone prediction API error:",
        e
      );

      setError(
        `${e.message}. Check that the backend is running on port 8000.`
      );
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    load();

    const interval = setInterval(
      load,
      60000
    );

    return () =>
      clearInterval(interval);
  }, []);

  // ============================================================
  // SELECTED PREDICTION
  // ============================================================

  const selected =
    predictions.find(
      (p) => p.id === selectedId
    );

  // ============================================================
  // MAP POINTS
  // ============================================================

  const points = predictions
    .filter(
      (p) =>
        typeof p.lat === "number" &&
        typeof p.lon === "number"
    )
    .map((p) => ({
      id: p.id,

      lat: p.lat,

      lon: p.lon,

      region: p.region,

      name: p.region,

      severity: p.severity,

      riskScore: p.riskScore,

      riskPct: p.riskPct,

      wind: p.wind,

      pressure: p.pressure,

      intensification:
        p.intensification,
    }));

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <div>
      <Breadcrumb
        trail={[
          "Dashboard",
          "Prediction",
          "Cyclone",
        ]}
      />

      <div className="p-5 max-w-7xl mx-auto space-y-4">

        {/* ==================================================
            HEADER
        ================================================== */}

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-2">

            <Wind
              className={`w-5 h-5 ${accentText(
                theme,
                "violet"
              )}`}
            />

            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Cyclone Prediction
            </h1>

          </div>

          <button
            onClick={load}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono uppercase tracking-widest border ${s.borderSoft} ${s.tint} ${s.textSecondary}`}
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
            INFORMATION
        ================================================== */}

        <div
          className={`rounded border border-dashed border-violet-400/30 bg-violet-400/5 text-[11px] font-mono px-4 py-2.5 ${accentText(
            theme,
            "violet"
          )}`}
        >
          Cyclone prediction is forecast-only.
          Markers show the latest prediction for
          each cyclone region. Prediction does not
          represent a confirmed cyclone event.
        </div>

        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">
            Failed to reach backend: {error}
          </div>
        )}

        {/* ==================================================
            MAP + LOG
        ================================================== */}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* ===========================
              MAP
          =========================== */}

          <div className="lg:col-span-2">

            <Panel
              title="Cyclone Risk Prediction Map"
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

          {/* ===========================
              PREDICTION LOG
          =========================== */}

          <Panel
            title="Prediction Log"
            icon={BellRing}
            accent="violet"
            dashed
          >

            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">

              {loading &&
                predictions.length === 0 && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    Loading cyclone predictions…
                  </div>
                )}

              {!loading &&
                predictions.length === 0 &&
                !error && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    No cyclone predictions yet.
                  </div>
                )}

              {predictions.map((p) => (

                <button
                  key={p.id}
                  onClick={() =>
                    setSelectedId(p.id)
                  }
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    p.id === selectedId
                      ? "border-violet-400/60 bg-violet-400/10"
                      : `${s.borderFaint} hover:border-violet-400/30`
                  }`}
                >

                  <div className="flex items-center justify-between mb-1">

                    <span
                      className={`text-xs font-mono ${s.textPrimary}`}
                    >
                      {p.region}
                    </span>

                    <SevBadge
                      severity={p.severity}
                    />

                  </div>

                  <div
                    className={`text-[10px] font-mono ${s.textMuted}`}
                  >
                    {p.riskPct}% risk ·{" "}
                    {p.generated}
                  </div>

                </button>

              ))}

            </div>

          </Panel>

        </div>

        {/* ==================================================
            SELECTED DETAILS
        ================================================== */}

        {selected && (

          <Panel
            title={`Prediction Detail — ${selected.region}`}
            icon={Activity}
            accent="violet"
            dashed
            right={
              <SevBadge
                severity={
                  selected.severity
                }
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
                label="Risk Score"
                value={selected.riskScore.toFixed(4)}
                s={s}
              />

              <Field
                label="Risk %"
                value={`${selected.riskPct}%`}
                s={s}
              />

              <Field
                label="Prediction Probability"
                value={`${(
                  selected.probability * 100
                ).toFixed(2)}%`}
                s={s}
              />

              <Field
                label="Latitude"
                value={selected.lat}
                s={s}
              />

              <Field
                label="Longitude"
                value={selected.lon}
                s={s}
              />

              <Field
                label="Wind Speed"
                value={selected.wind}
                s={s}
              />

              <Field
                label="Pressure"
                value={selected.pressure}
                s={s}
              />

              <Field
                label="Storm Direction"
                value={
                  selected.stormDirection !== null
                    ? `${selected.stormDirection}°`
                    : "—"
                }
                s={s}
              />

              <Field
                label="Storm Speed"
                value={selected.stormSpeed}
                s={s}
              />

              <Field
                label="Wind Change"
                value={selected.windChange}
                s={s}
              />

              <Field
                label="Previous Wind"
                value={selected.previousWind}
                s={s}
              />

              <Field
                label="Distance To Land"
                value={selected.distanceToLand}
                s={s}
              />

              <Field
                label="Intensification"
                value={
                  selected.intensification
                    ? "YES"
                    : "NO"
                }
                s={s}
              />

              <Field
                label="Severity"
                value={selected.severity}
                s={s}
              />

              <Field
                label="Generated"
                value={selected.generated}
                s={s}
              />

            </div>

            <div
              className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              About this model: cyclone risk is
              calculated from the latest atmospheric
              features including wind speed, pressure,
              storm direction and storm movement.
              This is a forecast and not a confirmed
              cyclone event.
            </div>

          </Panel>

        )}

      </div>
    </div>
  );
}

// ============================================================
// FORMAT TIME
// ============================================================

function formatTime(iso) {
  try {
    return (
      new Date(iso)
        .toISOString()
        .replace("T", " ")
        .slice(0, 19) +
      " UTC"
    );
  } catch {
    return "Unknown time";
  }
}

// ============================================================
// FIELD
// ============================================================

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

