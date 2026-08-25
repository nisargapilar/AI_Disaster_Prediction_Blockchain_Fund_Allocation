const BASE_URL = "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export function fetchDetectedEarthquakes() {
  return get("/earthquake/detected-earthquake-events");
}

export function fetchPredictedEarthquakes() {
  return get("/earthquake/predicted-earthquake-events");
}

// Simple equirectangular projection so real lat/lon can sit on our stylized
// (non-literal) tactical map. x/y are percentages, clamped so markers never
// sit flush against the edge.
export function projectLatLon(lat, lon) {
  const x = ((lon + 180) / 360) * 100;
  const y = ((90 - lat) / 180) * 100;
  return { x: Math.min(97, Math.max(3, x)), y: Math.min(94, Math.max(6, y)) };
}

function fmtTime(iso) {
  return new Date(iso).toISOString().replace("T", " ").slice(0, 19) + " UTC";
}

// Maps a raw /earthquake/detected-earthquake-events row to what the UI needs.
export function normalizeDetection(raw) {
  const { x, y } = projectLatLon(raw.location.lat, raw.location.lon);
  return {
    id: raw.event_id,
    name: `${raw.location.region} — M${raw.input_data.magnitude}`,
    magnitude: raw.input_data.magnitude,
    depth: raw.input_data.depth,
    region: raw.location.region,
    coords: `${raw.location.lat.toFixed(3)}°, ${raw.location.lon.toFixed(3)}°`,
    severity: raw.severity_tier,
    riskScore: raw.risk_score,
    fundStatus: raw.fund_status,
    source: raw.source,
    detected: fmtTime(raw.event_time),
    x,
    y,
    rawLat: raw.location.lat,
    rawLon: raw.location.lon,
  };
}

// Predictions have no lat/lon — only a region string — and the backend
// re-runs inference every few minutes, so the same region shows up many
// times. We dedupe to the latest prediction per region, and place a marker
// only when that region string matches a currently-loaded detection (so we
// can borrow its coordinates). Everything still shows up in the list either way.
export function normalizeAndDedupePredictions(rawList, detections) {
  const latestByRegion = new Map();
  for (const p of rawList) {
    const existing = latestByRegion.get(p.region);
    if (
      !existing ||
      new Date(p.predicted_time) > new Date(existing.predicted_time)
    ) {
      latestByRegion.set(p.region, p);
    }
  }
  const detectionByRegion = new Map(detections.map((d) => [d.region, d]));

  return Array.from(latestByRegion.values())
    .sort((a, b) => new Date(b.predicted_time) - new Date(a.predicted_time))
    .map((p) => {
      const match = detectionByRegion.get(p.region);
      return {
        id: p.prediction_id,
        region: p.region,
        riskScore: p.risk_score,
        riskPct: Math.round(p.risk_score * 100),
        severity: p.severity_tier,
        generated: fmtTime(p.predicted_time),
        sequenceLength: p.input_data.sequence_length,
        basedOnCount: p.input_data.based_on_event_ids?.length ?? 0,
        isSimulated: p.is_simulated,
        x: match?.x,
        y: match?.y,
        rawLat: match?.rawLat,
        rawLon: match?.rawLon,
        hasPosition: !!match,
      };
    });
}
