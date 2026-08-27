const API_BASE = "http://127.0.0.1:8000";

export async function detectForestFire(lat, lon, radius = 0.5) {
  const url =
    `${API_BASE}/forest_fire/detect` +
    `?lat=${encodeURIComponent(lat)}` +
    `&lon=${encodeURIComponent(lon)}` +
    `&radius=${encodeURIComponent(radius)}`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Forest Fire API returned ${response.status}`);
  }

  return response.json();
}

export async function fetchForestFireEvents() {
  const response = await fetch(`${API_BASE}/forest_fire/events`);

  if (!response.ok) {
    throw new Error(`Forest Fire API returned ${response.status}`);
  }

  return response.json();
}