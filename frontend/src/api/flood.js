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
// LAT / LON PROJECTION
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
  if (!iso) {
    return "N/A";
  }

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
      raw.input_data?.rainfall ?? null,

    riverLevel:
      raw.input_data?.river_level ?? null,

    humidity:
      raw.input_data?.humidity ?? null,

    temperature:
      raw.input_data?.temperature ?? null,

    probability:
      raw.input_data?.probability ?? null,

    coords:
      hasPosition
        ? `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`
        : "N/A",

    severity:
      raw.severity_tier ||
      "low",

    riskScore:
      raw.risk_score ?? null,

    riskPct:
      raw.risk_score != null
        ? Math.round(
            Number(raw.risk_score) * 100
          )
        : null,

    fundStatus:
      raw.fund_status ?? null,

    source:
      raw.source ?? null,

    detected:
      fmtTime(raw.event_time),

    hasPosition,

    rawLat:
      hasPosition
        ? lat
        : null,

    rawLon:
      hasPosition
        ? lon
        : null,

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
// IMPORTANT:
// This matches PredictionModel /predicted-flood-events
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
    .map((p) => {

      // ======================================================
      // PredictionModel stores coordinates inside input_data
      // ======================================================

      const lat = Number(
        p.input_data?.latitude
      );

      const lon = Number(
        p.input_data?.longitude
      );

      const hasPosition =
        Number.isFinite(lat) &&
        Number.isFinite(lon) &&
        lat >= -90 &&
        lat <= 90 &&
        lon >= -180 &&
        lon <= 180;

      // ======================================================
      // REGION COMES DIRECTLY FROM PredictionModel
      // ======================================================

      const region =
        p.region ||
        p.input_data?.region ||
        "Unknown Region";

      // ======================================================
      // RETURN FRONTEND FORMAT
      // ======================================================

      return {
        // PredictionModel
        id:
          p.prediction_id,

        predictionId:
          p.prediction_id,

        disasterType:
          p.disaster_type,

        // Exact region from backend
        region: region,

        name: region,

        // PredictionModel uses predicted_time
        generated:
          fmtTime(
            p.predicted_time
          ),

        predictedTime:
          p.predicted_time,

        // Risk
        riskScore:
          p.risk_score ?? null,

        riskPct:
          p.risk_score != null
            ? Math.round(
                Number(p.risk_score) * 100
              )
            : null,

        severity:
          p.severity_tier ||
          "low",

        // ====================================================
        // INPUT DATA
        // ====================================================

        rainfall:
          p.input_data?.rainfall ??
          null,

        humidity:
          p.input_data?.humidity ??
          null,

        temperature:
          p.input_data?.temperature ??
          null,

        probability:
          p.input_data?.probability ??
          null,

        // Probability as percentage
        probabilityPct:
          p.input_data?.probability != null
            ? Math.round(
                Number(
                  p.input_data.probability
                ) * 100
              )
            : null,

        // ====================================================
        // COORDINATES
        // ====================================================

        rawLat:
          hasPosition
            ? lat
            : null,

        rawLon:
          hasPosition
            ? lon
            : null,

        hasPosition,

        x:
          hasPosition
            ? projectLatLon(
                lat,
                lon
              ).x
            : null,

        y:
          hasPosition
            ? projectLatLon(
                lat,
                lon
              ).y
            : null,

        coords:
          hasPosition
            ? `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`
            : "N/A",

        // ====================================================
        // MATCHED EVENT
        // ====================================================

        matchedEventId:
          p.matched_event_id ??
          null,

        basedOnCount:
          p.matched_event_id
            ? 1
            : 0,

        // ====================================================
        // SIMULATION
        // ====================================================

        isSimulated:
          Boolean(
            p.is_simulated
          ),

        // ====================================================
        // OTHER
        // ====================================================

        source:
          "prediction",

        fundStatus:
          "not_applicable",

        model:
          p.input_data?.model ||
          "rule_based_flood_model",
      };
    });
}