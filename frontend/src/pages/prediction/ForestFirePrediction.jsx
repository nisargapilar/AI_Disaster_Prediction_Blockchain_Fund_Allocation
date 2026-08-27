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

const API_BASE = "http://127.0.0.1:8000";

async function fetchForestFirePredictions() {
  const response = await fetch(
    `${API_BASE}/forest_fire/predicted-forest-fire-events`
  );

  if (!response.ok) {
    throw new Error(
      `Forest Fire Prediction API returned ${response.status}`
    );
  }

  return response.json();
}

export default function ForestFirePrediction({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);

  const [predictions, setPredictions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadPredictions() {
    setLoading(true);
    setError(null);

    try {
      const raw = await fetchForestFirePredictions();

      setPredictions(raw);

      if (raw.length && !selectedId) {
        setSelectedId(raw[0].prediction_id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPredictions();

    const interval = setInterval(loadPredictions, 30000);

    return () => clearInterval(interval);
  }, []);

  const selected = predictions.find(
    (p) => p.prediction_id === selectedId
  );

  /*
   * Prediction markers are shown only when the prediction
   * has a matching detected event.
   *
   * matched_event_id tells us whether the prediction is
   * connected to a real forest-fire event.
   */

  const points = predictions
    .filter((p) => p.matched_event_id && p.input_data)
    .map((p) => {
      const mlFeatures = p.input_data?.ml_features || {};

      const lat =
        mlFeatures.latitude ??
        p.input_data?.latitude ??
        null;

      const lon =
        mlFeatures.longitude ??
        p.input_data?.longitude ??
        null;

      return {
        id: p.prediction_id,
        lat: Number(lat),
        lon: Number(lon),
        severity: p.severity_tier || "low",
      };
    })
    .filter(
      (p) =>
        Number.isFinite(p.lat) &&
        Number.isFinite(p.lon)
    );

  return (
    <div>
      {/* HEADER / BREADCRUMB */}

      <div className="p-5 max-w-7xl mx-auto space-y-4">

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-2">

            <Flame
              className={`w-5 h-5 ${accentText(
                theme,
                "violet"
              )}`}
            />

            <h1
              className={`text-lg font-mono uppercase tracking-widest ${s.textPrimary}`}
            >
              Forest Fire Prediction
            </h1>

          </div>

          <button
            onClick={loadPredictions}
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

        {/* DESCRIPTION */}

        <div
          className={`text-xs font-mono ${s.textMuted}`}
        >
          Prediction is forecast-only. It does not confirm a
          fire and never moves fund status.
        </div>

        {/* ERROR */}

        {error && (
          <div className="rounded border border-rose-400/40 bg-rose-400/10 text-rose-400 text-xs font-mono px-4 py-3">

            Failed to reach Forest Fire prediction backend:
            {" "}
            {error}

            <br />

            Make sure FastAPI is running on
            {" "}
            http://127.0.0.1:8000

          </div>
        )}

        {/* MAP + PREDICTION LOG */}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* MAP */}

          <div className="lg:col-span-2">

            <Panel
              title="Forest Fire Risk Prediction Map"
              icon={MapPin}
              accent="violet"
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
            title="Forest Fire Prediction Log"
            icon={Database}
            accent="violet"
          >

            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">

              {loading && predictions.length === 0 && (
                <div
                  className={`text-xs font-mono ${s.textMuted}`}
                >
                  Loading predictions...
                </div>
              )}

              {!loading &&
                predictions.length === 0 &&
                !error && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    No forest fire predictions found.
                  </div>
                )}

              {predictions.map((p) => (

                <button
                  key={p.prediction_id}
                  onClick={() =>
                    setSelectedId(p.prediction_id)
                  }
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    p.prediction_id === selectedId
                      ? "border-violet-400/60 bg-violet-400/10"
                      : `${s.borderFaint} hover:border-violet-400/30`
                  }`}
                >

                  <div className="flex items-center justify-between mb-1">

                    <span
                      className={`text-xs font-mono ${s.textPrimary}`}
                    >
                      {p.region ||
                        "Forest Fire Prediction"}
                    </span>

                    <SevBadge
                      severity={
                        p.severity_tier || "low"
                      }
                    />

                  </div>

                  <div
                    className={`text-[10px] font-mono ${s.textMuted}`}
                  >

                    {Math.round(
                      Number(p.risk_score || 0)
                    )}
                    % risk
                    {" · "}
                    {p.predicted_time
                      ? new Date(
                          p.predicted_time
                        ).toLocaleString()
                      : "Unknown time"}

                  </div>

                </button>

              ))}

            </div>

          </Panel>

        </div>

        {/* PREDICTION DETAIL */}

        {selected && (

          <Panel
            title={`Prediction Detail — ${selected.prediction_id}`}
            icon={Activity}
            accent="violet"
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
                label="Risk %"
                value={
                  selected.risk_score != null
                    ? `${Number(
                        selected.risk_score
                      ).toFixed(1)}%`
                    : "—"
                }
                s={s}
              />

              <Field
                label="Region"
                value={selected.region}
                s={s}
              />

              <Field
                label="Generated"
                value={
                  selected.predicted_time
                    ? new Date(
                        selected.predicted_time
                      ).toISOString()
                    : "—"
                }
                s={s}
              />

              <Field
                label="Matched Event"
                value={
                  selected.matched_event_id
                    ? "Yes"
                    : "No"
                }
                s={s}
              />

              <Field
                label="Simulated"
                value={
                  selected.is_simulated
                    ? "Yes"
                    : "No"
                }
                s={s}
              />

              <Field
                label="Model"
                value={
                  selected.input_data?.model_type ||
                  "XGBClassifier"
                }
                s={s}
              />

            </div>

            {/* ML DETAILS */}

            {selected.input_data && (
              <div
                className={`mt-4 pt-4 border-t ${s.borderFaint}`}
              >

                <div
                  className={`text-[9px] uppercase tracking-widest ${s.textFaint} mb-3`}
                >
                  Forest Fire XGBoost Prediction
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

                  <Field
                    label="Model Confidence"
                    value={
                      selected.input_data
                        ?.model_confidence != null
                        ? `${(
                            Number(
                              selected.input_data
                                .model_confidence
                            ) * 100
                          ).toFixed(1)}%`
                        : "—"
                    }
                    s={s}
                  />

                  <Field
                    label="Brightness"
                    value={
                      selected.input_data
                        ?.brightness
                    }
                    s={s}
                  />

                  <Field
                    label="FRP"
                    value={
                      selected.input_data?.frp
                    }
                    s={s}
                  />

                  <Field
                    label="Confidence"
                    value={
                      selected.input_data
                        ?.confidence
                    }
                    s={s}
                  />

                </div>

                {/* CLASS PROBABILITIES */}

                {selected.input_data
                  ?.class_probabilities && (

                  <div className="mt-4">

                    <div
                      className={`text-[9px] uppercase tracking-widest ${s.textFaint} mb-2`}
                    >
                      Class Probabilities
                    </div>

                    <div className="grid grid-cols-3 gap-3">

                      <Probability
                        label="Low"
                        value={
                          selected.input_data
                            .class_probabilities
                            ?.low
                        }
                        s={s}
                      />

                      <Probability
                        label="Medium"
                        value={
                          selected.input_data
                            .class_probabilities
                            ?.medium
                        }
                        s={s}
                      />

                      <Probability
                        label="High"
                        value={
                          selected.input_data
                            .class_probabilities
                            ?.high
                        }
                        s={s}
                      />

                    </div>

                  </div>

                )}

              </div>
            )}

            <div
              className={`mt-4 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >

              Source: Forest Fire XGBoost model.
              Prediction is forecast-only and does not
              release funds.

            </div>

          </Panel>

        )}

      </div>
    </div>
  );
}


/* ============================================================
   FIELD
============================================================ */

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


/* ============================================================
   PROBABILITY
============================================================ */

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