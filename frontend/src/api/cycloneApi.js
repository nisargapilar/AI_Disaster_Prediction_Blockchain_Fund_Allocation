const BASE_URL = "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }

  return res.json();
}

// ============================================================
// CYCLONE DETECTION API
// ============================================================

export function fetchDetectedCyclones() {
  return get("/cyclone/detected-cyclone-events");
}

// ============================================================
// CYCLONE PREDICTION API
// ============================================================

export function fetchPredictedCyclones() {
  return get("/cyclone/predicted-cyclone-events");
}

// ============================================================
// LAT/LON → MAP POSITION
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
  return (
    new Date(iso).toISOString().replace("T", " ").slice(0, 19) +
    " UTC"
  );
}

// ============================================================
// NORMALIZE CYCLONE DETECTION
// ============================================================

export function normalizeCycloneDetection(raw) {
  const features = raw.input_data?.features || {};

  const lat = Number(features.LAT);
  const lon = Number(features.LON);

  const { x, y } = projectLatLon(lat, lon);

  return {
    id: raw.event_id,

    region: raw.region,

    name: raw.region,

    latitude: lat,
    longitude: lon,

    coords: `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`,

    windSpeed: features.WMO_WIND,
    pressure: features.WMO_PRES,

    stormDirection: features.STORM_DIR,
    stormSpeed: features.STORM_SPEED,

    distanceToLand: features.DIST2LAND,

    severity: raw.severity_tier,
    riskScore: raw.risk_score,

    detected: fmtTime(raw.event_time),

    source: raw.source,

    x,
    y,

    rawLat: lat,
    rawLon: lon,

    raw,
  };
}

// ============================================================
// NORMALIZE CYCLONE PREDICTION
// ============================================================

export function normalizeCyclonePrediction(raw) {
  const features = raw.input_data?.features || {};

  const lat = Number(features.LAT);
  const lon = Number(features.LON);

  const { x, y } = projectLatLon(lat, lon);

  return {
    id: raw.prediction_id,

    region: raw.region,

    riskScore: raw.risk_score,

    riskPct: Math.round(raw.risk_score * 100),

    severity: raw.severity_tier,

    generated: fmtTime(raw.predicted_time),

    predictedIntensification:
      raw.input_data?.predicted_intensification ?? false,

    predictionProbability:
      raw.input_data?.prediction_probability ?? raw.risk_score,

    latitude: lat,
    longitude: lon,

    coords: `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`,

    windSpeed: features.WMO_WIND,
    pressure: features.WMO_PRES,

    stormDirection: features.STORM_DIR,
    stormSpeed: features.STORM_SPEED,

    distanceToLand: features.DIST2LAND,

    x,
    y,

    rawLat: lat,
    rawLon: lon,

    hasPosition: !isNaN(lat) && !isNaN(lon),

    isSimulated: raw.is_simulated,

    raw,
  };
}