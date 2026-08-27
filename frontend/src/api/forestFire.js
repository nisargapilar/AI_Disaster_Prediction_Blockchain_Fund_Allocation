const API_BASE = "http://127.0.0.1:8000";

export async function detectForestFire(
  confidence = "high",
  frp = 80.0,
  lat = 15.3173,
  lon = 75.7139,
  region = "Simulated Forest Block"
) {
  const params = new URLSearchParams({
    confidence,
    frp,
    lat,
    lon,
    region,
  });

  const response = await fetch(
    `${API_BASE}/forest_fire/simulate-detection?${params.toString()}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error(`Forest Fire API returned ${response.status}`);
  }

  return response.json();
}

export async function fetchForestFireEvents() {
  const response = await fetch(
    `${API_BASE}/forest_fire/detected-forest-fire-events`
  );

  if (!response.ok) {
    throw new Error(`Forest Fire API returned ${response.status}`);
  }

  return response.json();
}