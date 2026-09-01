export async function requestUnsubscribeLink(email) {
  const res = await fetch(`${BASE_URL}/subscribe/unsubscribe-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json(); // { status: "if_subscribed_link_sent" }
}
