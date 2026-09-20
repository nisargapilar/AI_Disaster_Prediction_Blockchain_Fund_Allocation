const BASE_URL = "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `API error ${res.status}: ${path}`);
  }
  return res.json();
}

export function fetchDashboard() {
  return get("/api/blockchain/dashboard");
}

export function verifyBeneficiary(eventId, mockId) {
  return post("/api/blockchain/verify-beneficiary", {
    event_id: eventId,
    mock_id: mockId,
  });
}

function fmtTime(iso) {
  return new Date(iso).toISOString().replace("T", " ").slice(0, 19) + " UTC";
}

// Maps a raw /api/blockchain/dashboard event row to what the UI needs.
export function normalizeFundEvent(raw) {
  return {
    id: raw.event_id,
    disasterType: raw.disaster_type,
    region: raw.region,
    severity: raw.severity_tier,
    fundStatus: raw.fund_status,
    eventTime: fmtTime(raw.event_time),
    beneficiariesVerified: raw.beneficiaries_verified,
    distributionRecords: raw.distribution_records,
  };
}