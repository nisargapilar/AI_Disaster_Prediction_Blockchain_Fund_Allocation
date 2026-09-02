const BASE_URL = "http://127.0.0.1:8000";

export async function subscribe({ email, region, disaster_type }) {
  const res = await fetch(`${BASE_URL}/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, region, disaster_type }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(
      detail?.detail?.[0]?.msg ||
        detail?.detail ||
        `Subscribe failed (${res.status})`,
    );
  }
  return res.json(); // { status: "pending_confirmation" }
}
export async function confirmSubscription(token) {
  const res = await fetch(
    `${BASE_URL}/subscribe/confirm/${encodeURIComponent(token)}`,
  );
  if (!res.ok) throw new Error(`Confirm failed (${res.status})`);
  return { status: "confirmed" };
}

// Self-service: email the user their unsubscribe token instead of requiring
// them to already have it in hand.
export async function requestUnsubscribeLink(email) {
  const res = await fetch(`${BASE_URL}/subscribe/unsubscribe-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json(); // { status: "if_subscribed_link_sent" }
}

// Mirrors the /subscribe/confirm/{token} pattern:
// GET /subscribe/unsubscribe/confirm/{token} returns HTML, not JSON, so we
// don't call res.json() here — just report success/failure.
export async function unsubscribe(token) {
  const res = await fetch(
    `${BASE_URL}/subscribe/unsubscribe/confirm/${encodeURIComponent(token)}`,
  );
  if (!res.ok) throw new Error(`Unsubscribe failed (${res.status})`);
  return { status: "unsubscribed" };
}

// Admin-only — forces the digest job to run immediately instead of waiting
// for its schedule. Useful for demos.
export async function digestNow() {
  const res = await fetch(`${BASE_URL}/subscribe/digest-now`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Digest trigger failed (${res.status})`);
  return res.json();
}
