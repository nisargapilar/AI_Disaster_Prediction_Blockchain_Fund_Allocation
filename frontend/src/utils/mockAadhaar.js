// Verhoeff checksum algorithm — same error-detection scheme used by real
// Aadhaar numbers. This generates structurally realistic mock IDs without
// using or resembling any real person's actual Aadhaar number.

const d = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
  [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
  [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
  [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
  [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
  [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
  [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
  [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
  [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
];
const p = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
  [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
  [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
  [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
  [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
  [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
  [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
];
const inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9];

function verhoeffChecksum(numStr) {
  let c = 0;
  const digits = numStr.split("").reverse().map(Number);
  digits.forEach((digit, i) => {
    c = d[c][p[i % 8][digit]];
  });
  return inv[c];
}

// Generates an 11-digit random base, appends a Verhoeff check digit -> 12 digits.
export function generateMockAadhaarId() {
  let base = "";
  for (let i = 0; i < 11; i++) {
    base += Math.floor(Math.random() * 10);
  }
  const check = verhoeffChecksum(base);
  return base + check;
}

export function isValidMockAadhaarId(id) {
  if (!/^\d{12}$/.test(id)) return false;
  const base = id.slice(0, 11);
  const check = parseInt(id[11], 10);
  return verhoeffChecksum(base) === check;
}

// Small pool of placeholder names — clearly fictional, used only to make
// each generated mock beneficiary card distinct for demo purposes.
const MOCK_NAME_POOL = [
  "Priya Sharma",
  "Arjun Patel",
  "Ananya Reddy",
  "Vikram Nair",
  "Sneha Iyer",
  "Rahul Verma",
  "Kavya Menon",
  "Aditya Rao",
  "Meera Pillai",
  "Rohan Gupta",
];

export function pickMockName() {
  const idx = Math.floor(Math.random() * MOCK_NAME_POOL.length);
  return MOCK_NAME_POOL[idx];
}

// Convenience: generates a full mock beneficiary (id + name) in one call.
export function generateMockBeneficiary() {
  return {
    id: generateMockAadhaarId(),
    name: pickMockName(),
  };
}

// Builds the JSON payload encoded into the QR — mirrors (in simplified
// form) how a real Aadhaar Secure QR carries signed demographic data.
// mockSignature is NOT real cryptographic signing — it's a simple hash
// labeled clearly as mock, so the pattern is visible without pretending
// to implement real UIDAI-grade security.
export function buildBeneficiaryPayload(mockId, mockName) {
  const payload = {
    id: mockId,
    name: mockName,
    issued: new Date().toISOString().slice(0, 10),
  };
  const raw = `${payload.id}|${payload.name}|${payload.issued}`;
  let hash = 0;
  for (let i = 0; i < raw.length; i++) {
    hash = (hash * 31 + raw.charCodeAt(i)) >>> 0;
  }
  payload.mockSignature = hash.toString(16);
  return payload;
}
