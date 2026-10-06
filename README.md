# Disaster Relief Transparency Platform

A disaster response system that connects **real-time detection**, **early-warning prediction**, **milestone-gated blockchain fund release**, and **verifiable beneficiary confirmation** — so that relief funds can be tracked from disaster event to actual aid delivery, publicly and auditably.

## The Problem

Disaster relief funds are often released in a lump sum with no verifiable link between money sent and aid actually delivered. This project closes that gap: funds unlock incrementally, tied to on-chain proof that real beneficiaries received aid — not just proof that money left a wallet.

## How It Works (End-to-End Flow)

```
Prediction (early warning) → SMS alert to region contact
         ↓
Detection (confirmed real event, e.g. USGS earthquake) → severity check
         ↓
high/critical severity → fund_status: pending
         ↓
Blockchain trigger → initial partial tranche (e.g. 30%) released to NGO/govt wallet
         ↓
NGO procures relief goods per fixed per-person entitlement standards
         ↓
Beneficiary self-scans mock-Aadhaar-style ID at distribution point
         ↓
Backend hashes ID → writes hash on-chain (verifiedBeneficiaries)
                  → writes full record off-chain (distribution_records)
         ↓
Once confirmed-beneficiary ratio hits milestone threshold → next tranche unlocks
         ↓
Public dashboard shows the full chain: prediction → detection → funds released
→ beneficiaries confirmed → completion % — visible to anyone
```

Prediction only informs (SMS alerts); **only confirmed detection** can move funds toward release.

## Architecture

### 1. Detection Modules (4x: earthquake, flood, cyclone, forest fire)

Poll authoritative data sources to confirm real disaster events and compute a severity tier. Each module writes into a shared `events` table, with `disaster_type` as a discriminator and disaster-specific fields stored in JSONB.

| Module      | Status         | Source                                     | Notes                                                     |
| ----------- | -------------- | ------------------------------------------ | --------------------------------------------------------- |
| Earthquake  | ✅ Complete    | USGS `all_hour.geojson` (polled every 30s) | Dedupes via `external_id`; `/simulate` endpoint for demos |
| Flood       | 🚧 In progress | Rainfall/river-level data                  | Own thresholds, same pattern                              |
| Cyclone     | 🚧 In progress | Wind speed/pressure (5 coastal stations)   | All currently low tier                                    |
| Forest fire | ⬜ Not started | NASA FIRMS thermal anomaly feed            | Planned XGBoost severity scoring                          |

### 2. Prediction Modules (4x)

Early-warning only — informational, kept in a separate `predictions` table, and **never** touches `fund_status`.

- **Earthquake (trained):** CNN-LSTM trained on 72,495 real USGS events (2015–2025, M≥4.5), benchmarked against XGBoost and plain LSTM baselines. Honest finding: all three hover near random (ROC-AUC ~0.50–0.52) — magnitude prediction from location/depth/time alone is a known unsolved problem in seismology. Documented as a relative risk indicator, not a reliable predictor.
- **Flood/cyclone/forest fire:** same architecture pattern, per-module features and thresholds.
- **Inference:** model + scaler loaded at FastAPI startup; every 5 minutes, pulls the last 20 events, builds a feature sequence, runs inference, writes `risk_score` + `severity_tier`.

### 3. Backend Infrastructure

- `db.py` — Supabase Postgres via Session pooler (IPv4-compatible), SQLAlchemy async + asyncpg
- `models.py` — shared `EventModel`, `PredictionModel`
- `main.py` — mounts each module's router, starts pollers/predictors as background asyncio tasks
- Per-module layout: `modules/<disaster>/{config.py, severity.py, detection.py, prediction.py, routes.py}`
- Two isolated Python environments: `backend/venv` (FastAPI/SQLAlchemy) and `ml_training/venv-ml` (TensorFlow/scikit-learn/XGBoost)

### 4. Database Tables

| Table                          | Purpose                                                                             |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| `events`                       | Confirmed detections; `fund_status`: `not_applicable → pending → released → failed` |
| `predictions`                  | Forecasts only — no `fund_status` column, by design                                 |
| `regions`                      | Wallet address + contact phone per region                                           |
| `fund_transactions`            | Milestone-based partial tranches (not lump sum)                                     |
| `relief_kit_standards`         | Fixed per-person entitlement by disaster type + severity                            |
| `distribution_records`         | Per-beneficiary confirmation, hashed ID, quantities, verification                   |
| `audit_log` / `model_versions` | Optional, not built, low priority                                                   |

### 5. Blockchain Layer (Solidity + Hardhat, Polygon testnet) — _not yet started_

- **Roles:** `owner` (deploys/configures), `triggerAuthority` (backend wallet, sole caller of `releaseFunds()`)
- **Milestone-gated release:** initial partial tranche unlocks on detection; further tranches unlock only once a minimum confirmed-beneficiary ratio is recorded on-chain per region
- **On-chain beneficiary verification:** `mapping(bytes32 => bool) verifiedBeneficiaries` — backend hashes the beneficiary ID and writes only the hash on-chain, never the raw ID
- `fund_dispatcher.py` — watches for `fund_status: pending`, releases the first tranche; a second process handles subsequent tranches
- Public chain gives built-in auditability of fund movement and beneficiary confirmations — no separate auditor role needed

### 6. Notification Layer — _planned_

SMS via Twilio to `regions.contact_phone` on high/critical severity. Recipients are contact records, not app users — no login required.

### 7. Fund Distribution & Accountability

- Funds released incrementally, gated behind confirmed distribution milestones
- Beneficiaries self-scan a **mock/simulated** Aadhaar-style ID — independent of NGO data entry, so confirmations can't be fabricated by the fund recipient
- Real UIDAI Aadhaar integration is explicitly out of scope (requires AUA/KUA licensing) — simulated throughout, documented as such
- Public dashboard shows funds released vs. beneficiaries confirmed vs. expected, making any gap visible — this is the project's core transparency claim

### 8. Roles

- **App-level:** Admin (full access, simulations, thresholds) · Viewer (public, read-only, no login)
- **Blockchain-level:** Owner (contract config) · Trigger Authority (backend wallet)
- **Fund-flow:** Distributing org/NGO (receives tranches, must hit milestones) · Beneficiary (self-verifies via hashed ID scan)

### 9. Frontend — _just starting_

React + Vite + Tailwind + Recharts. Planned: live Leaflet map of events, WebSocket event feed, prediction risk-score charts, fund-status indicators, and a released-vs-confirmed-beneficiaries comparison view.

## Current Status

| Component                         | Status                                                 |
| --------------------------------- | ------------------------------------------------------ |
| Earthquake detection & prediction | ✅ Built, tested end-to-end against real Supabase data |
| Flood / cyclone detection         | 🚧 In progress                                         |
| Forest fire                       | ⬜ Not started                                         |
| Blockchain (milestone/hash logic) | ⬜ Designed, not built                                 |
| SMS notifications                 | ⬜ Designed, not built                                 |
| Distribution tracking             | ⬜ Designed, not built                                 |
| Frontend                          | ⬜ Designed, not built                                 |

new

# Blockchain Fund Release & Mock-Aadhaar Beneficiary Verification

## System Documentation

**Project:** AI Disaster Prediction & Blockchain Fund Allocation System
**Network:** Polygon Amoy Testnet
**Contract Address:** `0x5D556C4307932FF613c80dEB8dF600378E401EC5`

---

## 1. Purpose & Design Philosophy

This subsystem exists to solve one specific problem in disaster relief: **how do you release emergency funds to an NGO quickly, while making it impossible for that NGO to quietly misappropriate the money?**

The answer implemented here is a two-step, two-transaction accountability model:

1. **Fund Release** — when a disaster event is confirmed and crosses a severity threshold, funds move from the smart contract to the NGO's wallet. This is fast and unconditional (the NGO needs money _before_ it can buy and distribute relief supplies).
2. **Beneficiary Verification** — after the NGO distributes physical aid (e.g. survival kits) to an affected person, that person's identity is confirmed and permanently recorded on-chain via a scanned mock-Aadhaar QR code. This creates a public, tamper-proof trail of _who actually received help_.

Because both the fund release and every beneficiary verification are public blockchain transactions, anyone — auditors, journalists, the public — can independently check whether the number of people an NGO claims to have helped lines up with the number of verified on-chain confirmations. The system doesn't prevent an NGO from behaving badly, but it makes it very difficult to hide if they do.

---

## 2. High-Level Architecture

```
┌─────────────────┐        ┌──────────────────┐        ┌────────────────────┐
│  Detection /     │───────▶│   FastAPI         │───────▶│  Smart Contract      │
│  Prediction      │  event │   Backend         │  tx    │  (Polygon Amoy)      │
│  Modules         │        │                   │        │                      │
└─────────────────┘        │  - events table    │        │  releaseFunds()      │
                            │  - distribution_   │        │  verifyBeneficiary() │
                            │    records table   │        │  isBeneficiaryVerified│
                            └──────────┬─────────┘        └──────────┬──────────┘
                                       │                              │
                                       │ REST API                    │ reads
                                       ▼                              ▼
                            ┌─────────────────────┐       ┌─────────────────────┐
                            │  React Frontend       │       │  PolygonScan          │
                            │                       │       │  (public explorer)    │
                            │  - Funds ledger       │       └─────────────────────┘
                            │  - Verify Beneficiary │
                            │  - ID Card generator  │
                            │  - Verified list      │
                            └─────────────────────┘
```

**Two separate concerns, two separate functions on the same contract:**

| Function                            | Who calls it                                                              | What it does                                                             | Moves money?                        |
| ----------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------- |
| `releaseFunds()`                    | Backend, as "trigger authority", when an event is confirmed fund-eligible | Sends POL from the contract to the NGO wallet                            | **Yes**                             |
| `verifyBeneficiary(hash, recordId)` | Backend, after a beneficiary scans their mock-Aadhaar QR                  | Records on-chain that this beneficiary-hash was confirmed for this event | **No** (0 POL value; only pays gas) |

---

## 3. The Mock-Aadhaar Identity Layer

Real Aadhaar numbers cannot and should not be used in a demo system. Instead, a structurally realistic but entirely fictional identity scheme was built, mirroring how real Aadhaar numbers are validated without using or resembling any real person's ID.

### 3.1 Verhoeff Checksum

Real Aadhaar numbers use the **Verhoeff algorithm** as a check-digit scheme to detect data-entry errors. This project implements the same algorithm for its mock IDs, purely for structural realism — it is not a security measure and makes no claim to be.

File: `src/utils/mockAadhaar.js`

```javascript
function verhoeffChecksum(numStr) {
  let c = 0;
  const digits = numStr.split("").reverse().map(Number);
  digits.forEach((digit, i) => {
    c = d[c][p[i % 8][digit]];
  });
  return inv[c];
}
```

- `generateMockAadhaarId()` — generates an 11-digit random base and appends a Verhoeff check digit, producing a realistic 12-digit mock ID.
- `isValidMockAadhaarId(id)` — validates a 12-digit ID against the checksum, confirming structural validity (used for input sanity-checking, not identity verification).

### 3.2 Mock Name Pool

To simulate multiple distinct beneficiaries (rather than one ID scanned repeatedly), each generated card is paired with a randomly selected name from a small, clearly fictional pool:

```javascript
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
```

`pickMockName()` selects one at random; `generateMockBeneficiary()` combines a fresh ID and name into one beneficiary object.

### 3.3 QR Payload Structure

Each beneficiary card encodes a JSON payload into its QR code, loosely mirroring (in simplified, non-cryptographic form) how a real Aadhaar Secure QR carries signed demographic data:

```javascript
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
```

**Payload shape:**

```json
{
  "id": "12345678901X",
  "name": "Vikram Nair",
  "issued": "2026-10-06",
  "mockSignature": "a1b2c3"
}
```

> **Important clarification:** `mockSignature` is explicitly **not** real cryptographic signing. It's a simple non-cryptographic checksum included to demonstrate the _pattern_ of a signed QR payload (as real Aadhaar Secure QR codes are signed by UIDAI) without claiming or implying production-grade security. This is clearly labeled in code comments to avoid any false impression of real security guarantees.

### 3.4 Beneficiary Card Page (`BeneficiaryCard.jsx`)

A dedicated page, separate from Funds/Verify, that:

- Generates a new mock beneficiary (ID + name) on load, and on demand via a "new card" button
- Renders the QR code using `qrcode.react`'s `QRCodeSVG` component
- Displays the name, mock ID, and issue date beneath the QR
- Includes a visible "simulation only — not a real ID" badge, so the fictional nature of the card is never ambiguous
- Has a print button (`window.print()`) so cards can be printed and physically scanned, simulating a real beneficiary presenting ID in the field

---

## 4. QR Scanning (Verification Entry Point)

File: `src/pages/funds/VerifyBeneficiary.jsx`

The verify page uses `html5-qrcode`'s `Html5QrcodeScanner` to activate the device camera and read a QR code in real time.

### 4.1 Scanner Lifecycle

The scanner is mounted/unmounted via a toggle button and a `useEffect` keyed on a `showScanner` boolean, so the camera is only ever active while the user has explicitly opened it:

```javascript
useEffect(() => {
  if (!showScanner) return;

  const scanner = new Html5QrcodeScanner(
    "qr-scanner-box",
    { fps: 10, qrbox: 220 },
    false,
  );

  scanner.render(
    (decodedText) => {
      let scannedId = decodedText;
      let scannedName = "";
      try {
        const parsed = JSON.parse(decodedText);
        if (parsed.id) scannedId = parsed.id;
        if (parsed.name) scannedName = parsed.name;
      } catch {
        // not JSON — treat decodedText as the raw ID
      }
      setMockId(scannedId);
      setMockName(scannedName);
      setShowScanner(false);
    },
    () => {}, // ignore per-frame scan failures — expected while camera searches
  );

  return () => {
    scanner.clear().catch(() => {});
  };
}, [showScanner]);
```

**Key design points:**

- The scanner decodes the full JSON payload, extracts `id` and `name`, and discards the rest (`issued`, `mockSignature` are not currently used downstream — they exist for structural realism on the card itself).
- A successful scan auto-fills the form and immediately closes the scanner, minimizing camera-open time.
- A fallback exists: if the QR content isn't valid JSON, the raw decoded text is used directly as the ID — so the system degrades gracefully rather than failing hard.
- Per-frame scan failures (the camera searching for a QR code but not finding one yet) are silently ignored — this is expected, continuous behavior, not an error state.

### 4.2 Event Selection Is Independent of the Scan

The QR payload intentionally does **not** encode which disaster event the beneficiary is claiming relief for. The event is selected separately via a dropdown, scoped only to events where `fundStatus === "released"`:

```javascript
{
  events
    .filter((ev) => ev.fundStatus === "released")
    .map((ev) => (
      <option key={ev.id} value={ev.id}>
        {ev.disasterType} — {ev.region} ({ev.eventTime})
      </option>
    ));
}
```

This is a deliberate design choice: the same physical beneficiary card can be reused across multiple disaster events over time (e.g., the same person verified for an earthquake today and, if applicable, a flood event months later) without needing to print a new card per event.

The submit button is disabled until **both** an event is selected and a valid-length mock ID is present:

```javascript
disabled={verifying || !selectedEventId || mockId.length < 4}
```

---

## 5. Backend: Verification Pipeline

### 5.1 Route Layer

File: `modules/blockchain/routes.py` (prefix: `/api/blockchain`)

```python
class VerifyBeneficiaryRequest(BaseModel):
    event_id: str
    mock_id: str
    mock_name: str | None = None


@router.post("/verify-beneficiary")
async def verify_beneficiary_endpoint(payload: VerifyBeneficiaryRequest):
    # Confirm the event exists
    async with async_session() as session:
        result = await session.execute(
            select(EventModel).where(EventModel.event_id == payload.event_id)
        )
        event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if len(payload.mock_id) < 4:
        raise HTTPException(status_code=400, detail="mock_id must be at least 4 characters")

    outcome = await verify_beneficiary(
        event_id=payload.event_id,
        mock_id=payload.mock_id,
        mock_name=payload.mock_name,
    )

    if outcome["status"] == "failed":
        raise HTTPException(status_code=500, detail=outcome.get("error", "Verification failed"))

    return outcome
```

**Validation performed before any blockchain interaction:**

1. The `event_id` must correspond to a real row in the `events` table (404 if not).
2. `mock_id` must be at least 4 characters (400 if not) — a minimal sanity check, not full checksum validation.

### 5.2 Service Layer (Core Logic)

File: `modules/blockchain/verify.py`

```python
async def verify_beneficiary(event_id: str, mock_id: str, mock_name: str | None = None) -> dict:
    beneficiary_hash = Web3.keccak(text=mock_id)
    beneficiary_hash_hex = beneficiary_hash.hex()

    async with async_session() as session:
        record = DistributionRecordModel(
            event_id=event_id,
            mock_name=mock_name,
            beneficiary_hash=beneficiary_hash_hex,
            mock_id_last4=mock_id[-4:] if len(mock_id) >= 4 else mock_id,
            status="pending",
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        already = contract.functions.isBeneficiaryVerified(beneficiary_hash).call()
        if already:
            record.status = "already_verified"
            await session.commit()
            return {"status": "already_verified", "record_id": str(record.record_id)}

        fn = contract.functions.verifyBeneficiary(beneficiary_hash, str(record.record_id))
        try:
            tx_hash, receipt = send_transaction(fn)
            record.status = "verified"
            record.tx_hash = tx_hash
            await session.commit()
            return {
                "status": "verified",
                "record_id": str(record.record_id),
                "tx_hash": tx_hash,
                "beneficiary_hash": beneficiary_hash_hex,
                "block": receipt.blockNumber,
            }
        except Exception as e:
            record.status = "failed"
            await session.commit()
            return {"status": "failed", "error": str(e), "record_id": str(record.record_id)}
```

**Step-by-step flow:**

1. **Hash the mock ID.** The raw mock Aadhaar number is immediately converted to a Keccak-256 hash (`Web3.keccak`). The raw ID is never persisted anywhere, on-chain or off — only its hash and the last 4 digits (for human-readable display/audit) are stored.
2. **Insert a database record immediately**, with `status = "pending"`, _before_ any blockchain call is attempted. This ensures every verification attempt is logged, even ones that later fail on-chain — nothing is silently lost.
3. **Check for a duplicate on-chain.** `isBeneficiaryVerified(hash)` is a read-only contract call (no gas, no transaction) that checks whether this beneficiary hash has already been verified at the contract level. This guards against duplicate-scan fraud — if someone tries to claim twice using the same ID, it's caught here.
   - If already verified → the database record's status is updated to `"already_verified"` and the function returns immediately. No new transaction is sent.
4. **Send the verification transaction.** If not a duplicate, `verifyBeneficiary(hash, recordId)` is called as a real state-changing transaction, signed and broadcast by the backend's configured wallet.
5. **Handle the outcome:**
   - **Success** → the database record is updated with `status = "verified"` and the real `tx_hash`, and the response includes the hash, record ID, and block number.
   - **Failure** (any exception — e.g. gas issues, network issues, contract revert) → the record is updated to `status = "failed"`, and the error message is captured and returned.

### 5.3 Database Schema

Table: `distribution_records`

| Column             | Type                          | Nullable | Purpose                                                                                                                   |
| ------------------ | ----------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| `record_id`        | UUID (PK)                     | No       | Unique identifier for this verification attempt                                                                           |
| `event_id`         | UUID (FK → `events.event_id`) | No       | Which disaster event this verification is tied to                                                                         |
| `mock_name`        | String                        | Yes      | Beneficiary's display name, captured from the scanned QR (only present for verifications done after this field was added) |
| `beneficiary_hash` | String                        | No       | Keccak-256 hash of the mock ID — the identity reference used both in the DB and on-chain                                  |
| `mock_id_last4`    | String                        | Yes      | Last 4 digits of the raw mock ID, kept for human-readable audit display without exposing the full ID                      |
| `tx_hash`          | String                        | Yes      | On-chain transaction hash, populated only on successful verification                                                      |
| `status`           | String                        | No       | One of: `pending`, `verified`, `already_verified`, `failed`                                                               |
| `created_at`       | Timestamp                     | —        | Auto-populated on insert                                                                                                  |

**Privacy design note:** The schema deliberately never stores the raw mock Aadhaar ID in full — only a one-way hash and the last 4 digits. This mirrors a reasonable real-world pattern for identity-verification systems: proving someone was checked without retaining their full identifying number in a queryable database.

### 5.4 Read Endpoint (Dashboard)

File: `modules/blockchain/routes.py`

```python
@router.get("/dashboard")
async def dashboard():
    # ... fetches fund-eligible events and joins their distribution_records ...
    return {
        "events": [
            {
                "event_id": str(e.event_id),
                "disaster_type": e.disaster_type,
                "region": e.region,
                "severity_tier": e.severity_tier,
                "fund_status": e.fund_status,
                "event_time": e.event_time.isoformat(),
                "beneficiaries_verified": len([
                    r for r in records_by_event.get(str(e.event_id), [])
                    if r["status"] == "verified"
                ]),
                "distribution_records": records_by_event.get(str(e.event_id), []),
            }
            for e in events
        ]
    }
```

This single endpoint serves both the Funds ledger page (event-level summary, including a live `beneficiaries_verified` count) and the Verified Beneficiaries page (full per-event list of individual verification records, including name, last-4 ID, status, and tx hash).

---

## 6. Smart Contract Interface

> The on-chain contract's Solidity source was designed and iterated on during development; the functions referenced throughout this document are the two primary entry points exposed to the backend:

### `releaseFunds(...)`

- Called by the backend acting as the "trigger authority" when a detected (not predicted) disaster event crosses the configured severity threshold.
- Transfers POL from the contract's balance to the configured NGO wallet address.
- Confirmed on-chain: multiple `0.005 POL` internal transactions from the contract address (`0x5D556C43...78E401EC5`) to the NGO wallet (`0x798B03dF...c3AEB25Db`) are visible via PolygonScan's "Internal Transactions" tab for that address.

### `verifyBeneficiary(bytes32 beneficiaryHash, string recordId)`

- Called by the backend after a beneficiary's mock ID is hashed.
- Records the beneficiary hash as verified on-chain, associated with the backend's internal `recordId` for cross-referencing with the off-chain database.
- Sends **0 POL** in value — this transaction's cost is purely gas (observed: ~0.0034 POL gas fee per call on Amoy), since no funds are moved by this function. Its sole purpose is creating an immutable, public record.

### `isBeneficiaryVerified(bytes32 beneficiaryHash) → bool`

- A read-only (`view`) function, callable with no gas cost and no transaction.
- Used by the backend to check for duplicate verification attempts before sending a real transaction.

---

## 7. Frontend Page Structure

The feature is split across four distinct, independently-routed pages (not nested tabs), consistent with the rest of the application's `view`/`setView` string-based routing in `App.jsx`:

| Page     | Route (`view` value) | File                                    | Purpose                                                                                    |
| -------- | -------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------ |
| Funds    | `funds`              | `pages/funds/FundsPlaceholder.jsx`      | Ledger of all fund-eligible events, their release status, and verified-beneficiary counts  |
| Verify   | `verify-beneficiary` | `pages/funds/VerifyBeneficiary.jsx`     | Scan or manually enter a beneficiary ID, select an event, submit for on-chain verification |
| ID Card  | `beneficiary-card`   | `pages/funds/BeneficiaryCard.jsx`       | Generate and print a mock beneficiary QR card                                              |
| Verified | `verified-list`      | `pages/funds/VerifiedBeneficiaries.jsx` | Full audit list of every verification record, grouped by event                             |

Each page is wired into `Navbar.jsx`'s `items` array and `App.jsx`'s view-routing `if`/`else if` chain, following the existing pattern used by Detection and Prediction pages.

---

## 8. End-to-End Verification Flow (Full Trace)

1. A beneficiary is given a printed card (generated via **ID Card** page) containing a QR-encoded `{ id, name, issued, mockSignature }` payload.
2. After receiving relief supplies from the NGO, the beneficiary's card is scanned at the **Verify** page.
3. The scanner decodes the QR, extracts `id` and `name`, and auto-fills the form.
4. The operator selects the correct disaster event from the dropdown (scoped to `released` events only).
5. On submit, the frontend calls `verifyBeneficiary(eventId, mockId, mockName)` → `POST /api/blockchain/verify-beneficiary`.
6. The backend validates the event exists and the ID meets minimum length, then:
   - Hashes the mock ID (Keccak-256)
   - Inserts a `pending` record into `distribution_records`
   - Checks on-chain for a prior verification of this hash
   - If new: sends a real `verifyBeneficiary()` transaction to the contract
   - Updates the database record with the final status and (if successful) the transaction hash
7. The frontend displays the result: `verified` with a clickable/visible tx hash, `already_verified`, or an error.
8. The **Verified Beneficiaries** page (re-fetched from `/api/blockchain/dashboard`) now shows this record under its event, with the beneficiary's name, last-4 ID, status, and tx hash — viewable by anyone with access to the dashboard, and independently verifiable by anyone via PolygonScan using the tx hash.

---

## 9. Verified Working — Evidence from Testing

During development, the following was independently confirmed via Polygon Amoy's block explorer (not just trusted from application responses):

**Fund release to NGO wallet** — confirmed via `https://amoy.polygonscan.com/address/0x798B03dF7F8Bf2AB8F7CCE4D2499116c3AEB25Db`:

- Three internal transactions, each `0.005 POL`, from the contract address to the NGO wallet
- NGO wallet balance: `0.115 POL` (cumulative across more than the 3 visible recent transactions)

**Beneficiary verification transaction** — confirmed via `https://amoy.polygonscan.com/tx/0x6428898e458f2a2da51448c528604a8d3210c4c16a348d4a09940b4dac87c34c`:

- Status: Success
- From: backend signer wallet (`0xc269f58d...EcA3e4929`)
- To: contract address (`0x5D556C43...78E401EC5`)
- **Value: 0 POL** (confirms no funds move during verification — record-only)
- Transaction fee: `0.003430652503572415 POL` (gas cost only)

This independently confirms both halves of the accountability design are functioning as intended: money moves only via `releaseFunds()` to the NGO, and `verifyBeneficiary()` is purely a record-keeping transaction with zero value transfer.

---

## 10. Known Limitations & Honest Caveats

- **`mockSignature` is not cryptographically secure.** It is a simple additive hash for demonstrating the _pattern_ of a signed QR payload, not real signature verification. This is intentional and documented in-code, but should be stated clearly in any presentation to avoid overstating the system's security properties.
- **No server-side check that `event_id` is fund-eligible/released** at the verification endpoint level — this is currently enforced only by the frontend dropdown filter. A direct API call bypassing the UI could submit a verification against a non-released event. Acceptable for a demo; would need a backend-side check for production use.
- **Older verification records lack a `mock_name`** — the field was added partway through development, so historical records show `"Unnamed"` in the UI. Only verifications performed after the schema migration carry a name.
- **`failed` status records do not currently surface their error reason in the frontend UI** — the error message is captured and stored in the backend's returned payload but not persisted to or displayed from the database long-term.
- **Beneficiary names, once captured, are stored in plaintext in the off-chain database** (though never on-chain). This is a deliberate trade-off for practical accountability (being able to answer "who did we help") against the stricter privacy-first design of showing only hashed/last-4 identifiers. Teams should decide and clearly state which privacy posture they're presenting.

---

## 11. Summary for Presentation

> _"When a disaster is confirmed, our smart contract releases funds directly to the responding NGO's wallet — publicly, on-chain, instantly auditable. The NGO buys and distributes survival kits. When a beneficiary receives their kit, they scan a mock-Aadhaar-style QR code, and that confirmation is permanently recorded on the blockchain — not in a database the NGO controls, but on a public ledger anyone can check. If an NGO claims to have helped 100 people but only 20 verifications appear on-chain, that gap is impossible to hide."_
