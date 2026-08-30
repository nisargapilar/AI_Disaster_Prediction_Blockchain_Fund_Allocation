import { useEffect, useState } from "react";
import {
  Waves,
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

import {
  Panel,
  SevBadge,
} from "../../components/ui";

import RealMap from "../../components/RealMap";
import Breadcrumb from "../../components/Breadcrumb";

import {
  fetchDetectedFloods,
  fetchPredictedFloods,
  normalizeFloodDetection,
  normalizeFloodPredictions,
} from "../../api/flood";

export default function FloodPrediction({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);

  const [predictions, setPredictions] =
    useState([]);

  const [detections, setDetections] =
    useState([]);

  const [selectedId, setSelectedId] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(null);

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const [
        rawPredicted,
        rawDetected,
      ] = await Promise.all([
        fetchPredictedFloods(),
        fetchDetectedFloods(),
      ]);

      const preds =
        normalizeFloodPredictions(
          rawPredicted
        );

      const detected =
        Array.isArray(rawDetected)
          ? rawDetected.map(
              normalizeFloodDetection
            )
          : [];

      console.log(
        "FLOOD PREDICTIONS:",
        preds
      );

      console.log(
        "FLOOD DETECTIONS:",
        detected
      );

      setPredictions(preds);
      setDetections(detected);

      if (
        preds.length > 0 &&
        !selectedId
      ) {
        setSelectedId(preds[0].id);
      }
    } catch (e) {
      console.error(
        "Flood prediction error:",
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

  const selected =
    predictions.find(
      (p) => p.id === selectedId
    );

  // ==========================================================
  // PREDICTION MAP
  //
  // Prediction records contain region but may not contain
  // latitude/longitude. Therefore we match predictions to
  // detected flood locations by region.
  // ==========================================================

  const points = predictions
    .map((p) => {
      const match =
        detections.find(
          (d) =>
            d.region &&
            p.region &&
            d.region.toLowerCase() ===
              p.region.toLowerCase()
        );

      if (!match) {
        return null;
      }

      if (
        !Number.isFinite(match.rawLat) ||
        !Number.isFinite(match.rawLon)
      ) {
        return null;
      }

      return {
        id: p.id,
        name: p.region,
        region: p.region,
        lat: match.rawLat,
        lon: match.rawLon,
        severity: p.severity,
      };
    })
    .filter(Boolean);

  return (
    <div>
      <Breadcrumb
        trail={[
          "Dashboard",
          "Prediction",
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
                "violet"
              )}`}
            />

            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Flood Prediction
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
            INFO
        ================================================== */}

        <div
          className={`rounded border border-dashed border-violet-400/30 bg-violet-400/5 text-[11px] font-mono px-4 py-2.5 ${accentText(
            theme,
            "violet"
          )}`}
        >
          Flood prediction is forecast-only.
          It does not release funds. Prediction
          markers are matched to known flood
          regions.
        </div>

        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">
            Failed to reach flood prediction
            backend: {error}
          </div>
        )}

        {/* ==================================================
            MAP + PREDICTION LOG
        ================================================== */}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* MAP */}

          <div className="lg:col-span-2">

            <Panel
              title="Flood Risk Prediction Map"
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

          {/* PREDICTION LOG */}

          <Panel
            title="Flood Prediction Log"
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
                    Loading flood predictions…
                  </div>
                )}

              {!loading &&
                predictions.length === 0 &&
                !error && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    No flood predictions yet.
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
                    {p.riskPct != null
                      ? `${p.riskPct}% risk`
                      : "Risk unavailable"}{" "}
                    · {p.generated}
                  </div>

                </button>
              ))}

            </div>

          </Panel>

        </div>

        {/* ==================================================
            PREDICTION DETAILS
        ================================================== */}

        {selected && (
          <Panel
            title={`Flood Prediction Detail — ${selected.id}`}
            icon={Activity}
            accent="violet"
            dashed
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
                label="Generated"
                value={selected.generated}
                s={s}
              />

              <Field
                label="Sequence Length"
                value={
                  selected.sequenceLength
                }
                s={s}
              />

              <Field
                label="Based On Events"
                value={
                  selected.basedOnCount
                }
                s={s}
              />

              <Field
                label="Simulated"
                value={
                  selected.isSimulated
                    ? "Yes"
                    : "No"
                }
                s={s}
              />

              <Field
                label="Map Position"
                value={
                  points.some(
                    (p) =>
                      p.id === selected.id
                  )
                    ? "Matched"
                    : "No match"
                }
                s={s}
              />

            </div>

            <div
              className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              Flood prediction is a forecast
              generated from recent flood data.
              It does not represent a confirmed
              flood event and does not directly
              release funds.
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