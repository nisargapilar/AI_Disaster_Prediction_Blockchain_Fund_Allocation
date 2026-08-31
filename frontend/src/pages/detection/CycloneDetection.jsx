
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

export default function CycloneDetection() {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ============================================================
  // LOAD REAL CYCLONE DETECTION EVENTS
  // ============================================================

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cyclone/detected-cyclone-events`
      );

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const rawEvents = await response.json();

      console.log("CYCLONE EVENTS FROM BACKEND:", rawEvents);

      // ========================================================
      // KEEP ONLY THE LATEST EVENT FOR EACH REGION
      //
      // IMPORTANT:
      // Region is inside event.location.region
      // ========================================================

      const latestByRegion = new Map();

      for (const event of rawEvents) {
        const region =
          event.location?.region || "Unknown";

        const existing =
          latestByRegion.get(region);

        if (
          !existing ||
          new Date(event.event_time) >
            new Date(existing.event_time)
        ) {
          latestByRegion.set(region, event);
        }
      }

      // ========================================================
      // NORMALIZE BACKEND DATA FOR UI
      // ========================================================

      const normalized = Array.from(
        latestByRegion.values()
      )
        .sort(
          (a, b) =>
            new Date(b.event_time) -
            new Date(a.event_time)
        )
        .map((event) => {
          // Region is inside location
          const region =
            event.location?.region || "Unknown";

          const lat =
            typeof event.location?.lat === "number"
              ? event.location.lat
              : null;

          const lon =
            typeof event.location?.lon === "number"
              ? event.location.lon
              : null;

          return {
            id: event.event_id,

            // ==================================================
            // FIXED REGION
            // ==================================================
            region: region,

            disasterType:
              event.disaster_type || "cyclone",

            source:
              event.source || "real",

            // ==================================================
            // LOCATION
            // ==================================================
            lat: lat,
            lon: lon,

            // ==================================================
            // ATMOSPHERIC DATA
            // ==================================================
            wind:
              event.input_data?.wind_speed ?? null,

            pressure:
              event.input_data?.pressure ?? null,

            // ==================================================
            // RISK
            // ==================================================
            riskScore:
              event.risk_score ?? 0,

            riskPct: Math.round(
              (event.risk_score ?? 0) * 100
            ),

            severity:
              event.severity_tier || "low",

            fundStatus:
              event.fund_status ||
              "not_applicable",

            eventTime:
              event.event_time,

            generated:
              formatTime(event.event_time),
          };
        });

      console.log(
        "NORMALIZED CYCLONE EVENTS:",
        normalized
      );

      setEvents(normalized);

      // ========================================================
      // SELECT FIRST EVENT
      // ========================================================

      if (normalized.length > 0) {
        setSelectedId((currentId) => {
          const stillExists = normalized.some(
            (event) => event.id === currentId
          );

          return stillExists
            ? currentId
            : normalized[0].id;
        });
      } else {
        setSelectedId(null);
      }
    } catch (e) {
      console.error(
        "Cyclone detection API error:",
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
  // SELECTED EVENT
  // ============================================================

  const selected =
    events.find(
      (event) => event.id === selectedId
    );

  // ============================================================
  // MAP POINTS
  // ============================================================

  const points = events
    .filter(
      (event) =>
        typeof event.lat === "number" &&
        typeof event.lon === "number"
    )
    .map((event) => ({
      id: event.id,

      lat: event.lat,

      lon: event.lon,

      // IMPORTANT:
      // This is now the actual region name
      region: event.region,

      name: event.region,

      severity: event.severity,

      riskScore: event.riskScore,

      riskPct: event.riskPct,

      wind: event.wind,

      pressure: event.pressure,

      source: event.source,
    }));

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <div>
      <Breadcrumb
        trail={[
          "Dashboard",
          "Detection",
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
              Cyclone Detection
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
          Cyclone detection uses real atmospheric
          observations. Markers show the latest
          detected event for each cyclone region.
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
            MAP + DETECTION LOG
        ================================================== */}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* ===========================
              MAP
          =========================== */}

          <div className="lg:col-span-2">

            <Panel
              title="Cyclone Detection Map"
              icon={MapPin}
              accent="violet"
              dashed
            >

              <RealMap
                points={points}
                selectedId={selectedId}
                onSelect={setSelectedId}
                mode="detection"
              />

            </Panel>

          </div>

          {/* ===========================
              DETECTION LOG
          =========================== */}

          <Panel
            title="Detection Log"
            icon={BellRing}
            accent="violet"
            dashed
          >

            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">

              {loading &&
                events.length === 0 && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    Loading cyclone detections…
                  </div>
                )}

              {!loading &&
                events.length === 0 &&
                !error && (
                  <div
                    className={`text-xs font-mono ${s.textMuted}`}
                  >
                    No cyclone detections yet.
                  </div>
                )}

              {events.map((event) => (

                <button
                  key={event.id}
                  onClick={() =>
                    setSelectedId(event.id)
                  }
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    event.id === selectedId
                      ? "border-violet-400/60 bg-violet-400/10"
                      : `${s.borderFaint} hover:border-violet-400/30`
                  }`}
                >

                  <div className="flex items-center justify-between mb-1">

                    <span
                      className={`text-xs font-mono ${s.textPrimary}`}
                    >
                      {event.region}
                    </span>

                    <SevBadge
                      severity={
                        event.severity
                      }
                    />

                  </div>

                  <div
                    className={`text-[10px] font-mono ${s.textMuted}`}
                  >
                    {event.riskPct}% risk ·{" "}
                    {event.generated}
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
            title={`Detection Detail — ${selected.region}`}
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
                label="Disaster Type"
                value={
                  selected.disasterType
                }
                s={s}
              />

              <Field
                label="Source"
                value={selected.source}
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
                label="Severity"
                value={selected.severity}
                s={s}
              />

              <Field
                label="Fund Status"
                value={selected.fundStatus}
                s={s}
              />

              <Field
                label="Event Time"
                value={selected.generated}
                s={s}
              />

              <Field
                label="Event ID"
                value={selected.id}
                s={s}
              />

            </div>

            <div
              className={`mt-3 pt-3 border-t ${s.borderFaint} text-[10px] font-mono ${s.textFaint}`}
            >
              About this detection: this event
              represents real atmospheric observations
              received by the cyclone detection system.
              The risk score and severity indicate the
              current detected risk level for this region.
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

