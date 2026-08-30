const BASE_URL = "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }

  return res.json();
}

// ============================================================
// FLOOD DETECTION API
// ============================================================

export function fetchDetectedFloods() {
  return get("/flood/detected-flood-events");
}

// ============================================================
// FLOOD PREDICTION API
// ============================================================

export function fetchPredictedFloods() {
  return get("/flood/predicted-flood-events");
}

// ============================================================
// LAT/LON
// ============================================================

export function projectLatLon(lat, lon) {
  const x = ((lon + 180) / 360) * 100;
  const y = ((90 - lat) / 180) * 100;

  return {
    x: Math.min(97, Math.max(3, x)),
    y: Math.min(94, Math.max(6, y)),
  };
}

// ============================================================
// TIME FORMAT
// ============================================================

function fmtTime(iso) {
  if (!iso) return "N/A";

  const date = new Date(iso);

  if (Number.isNaN(date.getTime())) {
    return "N/A";
  }

  return (
    date.toISOString().replace("T", " ").slice(0, 19) +
    " UTC"
  );
}

// ============================================================
// NORMALIZE FLOOD DETECTION
// ============================================================

export function normalizeFloodDetection(raw) {
  const lat = Number(raw.location?.lat);
  const lon = Number(raw.location?.lon);

  const hasPosition =
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180;

  return {
    id: raw.event_id,

    name:
      raw.location?.region ||
      "Unknown Region",

    region:
      raw.location?.region ||
      "Unknown Region",

    rainfall:
      raw.input_data?.rainfall,

    riverLevel:
      raw.input_data?.river_level,

    humidity:
      raw.input_data?.humidity,

    temperature:
      raw.input_data?.temperature,

    probability:
      raw.input_data?.probability,

    coords: hasPosition
      ? `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`
      : "N/A",

    severity:
      raw.severity_tier ||
      "low",

    riskScore:
      raw.risk_score,

    riskPct:
      raw.risk_score != null
        ? Math.round(
            Number(raw.risk_score) * 100
          )
        : null,

    fundStatus:
      raw.fund_status,

    source:
      raw.source,

    detected:
      fmtTime(raw.event_time),

    hasPosition,

    rawLat:
      hasPosition ? lat : null,

    rawLon:
      hasPosition ? lon : null,

    x:
      hasPosition
        ? projectLatLon(lat, lon).x
        : null,

    y:
      hasPosition
        ? projectLatLon(lat, lon).y
        : null,
  };
}

// ============================================================
// NORMALIZE FLOOD PREDICTIONS
// ============================================================

export function normalizeFloodPredictions(rawList) {
  if (!Array.isArray(rawList)) {
    return [];
  }

  return [...rawList]
    .sort(
      (a, b) =>
        new Date(b.predicted_time) -
        new Date(a.predicted_time)
    )
    .map((p) => ({
      id: p.prediction_id,

      region:
        p.region ||
        "Unknown Region",

      riskScore:
        p.risk_score,

      riskPct:
        p.risk_score != null
          ? Math.round(
              Number(p.risk_score) * 100
            )
          : null,

      severity:
        p.severity_tier ||
        "low",

      generated:
        fmtTime(p.predicted_time),

      sequenceLength:
        p.input_data?.sequence_length,

      basedOnCount:
        p.input_data?.based_on_event_ids
          ?.length ?? 0,

      isSimulated:
        p.is_simulated,
    }));
}