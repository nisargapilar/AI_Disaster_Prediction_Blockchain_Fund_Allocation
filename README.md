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

| Module | Status | Source | Notes |
|---|---|---|---|
| Earthquake | ✅ Complete | USGS `all_hour.geojson` (polled every 30s) | Dedupes via `external_id`; `/simulate` endpoint for demos |
| Flood | 🚧 In progress | Rainfall/river-level data | Own thresholds, same pattern |
| Cyclone | 🚧 In progress | Wind speed/pressure (5 coastal stations) | All currently low tier |
| Forest fire | ⬜ Not started | NASA FIRMS thermal anomaly feed | Planned XGBoost severity scoring |

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

| Table | Purpose |
|---|---|
| `events` | Confirmed detections; `fund_status`: `not_applicable → pending → released → failed` |
| `predictions` | Forecasts only — no `fund_status` column, by design |
| `regions` | Wallet address + contact phone per region |
| `fund_transactions` | Milestone-based partial tranches (not lump sum) |
| `relief_kit_standards` | Fixed per-person entitlement by disaster type + severity |
| `distribution_records` | Per-beneficiary confirmation, hashed ID, quantities, verification |
| `audit_log` / `model_versions` | Optional, not built, low priority |

### 5. Blockchain Layer (Solidity + Hardhat, Polygon testnet) — *not yet started*

- **Roles:** `owner` (deploys/configures), `triggerAuthority` (backend wallet, sole caller of `releaseFunds()`)
- **Milestone-gated release:** initial partial tranche unlocks on detection; further tranches unlock only once a minimum confirmed-beneficiary ratio is recorded on-chain per region
- **On-chain beneficiary verification:** `mapping(bytes32 => bool) verifiedBeneficiaries` — backend hashes the beneficiary ID and writes only the hash on-chain, never the raw ID
- `fund_dispatcher.py` — watches for `fund_status: pending`, releases the first tranche; a second process handles subsequent tranches
- Public chain gives built-in auditability of fund movement and beneficiary confirmations — no separate auditor role needed

### 6. Notification Layer — *planned*

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

### 9. Frontend — *just starting*

React + Vite + Tailwind + Recharts. Planned: live Leaflet map of events, WebSocket event feed, prediction risk-score charts, fund-status indicators, and a released-vs-confirmed-beneficiaries comparison view.

## Current Status

| Component | Status |
|---|---|
| Earthquake detection & prediction | ✅ Built, tested end-to-end against real Supabase data |
| Flood / cyclone detection | 🚧 In progress |
| Forest fire | ⬜ Not started |
| Blockchain (milestone/hash logic) | ⬜ Designed, not built |
| SMS notifications | ⬜ Designed, not built |
| Distribution tracking | ⬜ Designed, not built |
| Frontend | ⬜ Designed, not built |
