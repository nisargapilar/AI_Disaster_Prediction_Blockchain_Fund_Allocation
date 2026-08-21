"""
backend/modules/earthquake/prediction.py

Loads the trained CNN-LSTM model once at startup, then every N minutes
pulls the most recent 20 earthquake events (real + simulated, doesn't
matter which — same events table) and produces an early-warning
risk_score + severity_tier, written to the predictions table.

Never touches fund_status — predictions are informational only.
"""

import json
import asyncio
from datetime import datetime, timezone

import numpy as np
import joblib
from tensorflow.keras.models import load_model
from sqlalchemy import select

from modules.notify.dispatch import notify_subscribers

from db import async_session
from models import EventModel, PredictionModel

MODEL_PATH = "ml_artifacts/earthquake_cnn_lstm.keras"
SCALER_PATH = "ml_artifacts/earthquake_scaler.pkl"
FEATURE_REF_PATH = "ml_artifacts/earthquake_feature_reference.json"

SEVERITY_CONFIG_PATH = "config/severity_config.json"

PREDICTION_INTERVAL_SECONDS = 300  # every 5 minutes

model = load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

with open(FEATURE_REF_PATH) as f:
    feature_ref = json.load(f)

MEAN_LAT = feature_ref["mean_lat"]
MEAN_LON = feature_ref["mean_lon"]
SEQUENCE_LENGTH = feature_ref["sequence_length"]
FEATURES = feature_ref["features"]

with open(SEVERITY_CONFIG_PATH) as f:
    severity_config = json.load(f)["earthquake"]


def severity_tier_from_score(risk_score: float) -> str:
    for tier, (low, high) in severity_config.items():
        if low <= risk_score < high:
            return tier
    return "critical"


async def fetch_recent_events(session, limit: int = SEQUENCE_LENGTH):
    stmt = (
        select(EventModel)
        .where(EventModel.disaster_type == "earthquake")
        .order_by(EventModel.event_time.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return list(reversed(rows))


def build_feature_sequence(events):
    rows = []
    prev_time = None
    for ev in events:
        depth = ev.input_data.get("depth")
        lat, lon = ev.lat, ev.lon
        event_time = ev.event_time

        time_diff = 0.0 if prev_time is None else (event_time - prev_time).total_seconds() / 3600
        prev_time = event_time

        dist_to_center = np.sqrt((lat - MEAN_LAT) ** 2 + (lon - MEAN_LON) ** 2)

        rows.append([lat, lon, depth, time_diff, dist_to_center])

    arr = np.array(rows)
    scaled = scaler.transform(arr)
    return scaled.reshape(1, SEQUENCE_LENGTH, len(FEATURES))


async def run_prediction_once():
    async with async_session() as session:
        events = await fetch_recent_events(session)

        if len(events) < SEQUENCE_LENGTH:
            print(f"[prediction] Not enough events yet ({len(events)}/{SEQUENCE_LENGTH}) — skipping this cycle.")
            return

        X = build_feature_sequence(events)
        risk_score = float(model.predict(X, verbose=0)[0][0])
        severity_tier = severity_tier_from_score(risk_score)

        latest_event = events[-1]
        is_simulated = any(e.source != "real" for e in events)

        prediction_row = PredictionModel(
            disaster_type="earthquake",
            region=latest_event.region,
            predicted_time=datetime.now(timezone.utc),
            input_data={"sequence_length": SEQUENCE_LENGTH, "based_on_event_ids": [str(e.event_id) for e in events]},
            risk_score=risk_score,
            severity_tier=severity_tier,
            matched_event_id=None,
            is_simulated=is_simulated,
        )
        session.add(prediction_row)
        await session.commit()

        print(f"[prediction] region={latest_event.region} risk_score={risk_score:.4f} severity={severity_tier} simulated={is_simulated}")

        if severity_tier in ("high", "critical"):
            await notify_subscribers(session, "earthquake", latest_event.region, risk_score, severity_tier)


async def prediction_loop():
    while True:
        try:
            await run_prediction_once()
        except Exception as e:
            print(f"[prediction] ERROR: {e}")
        await asyncio.sleep(PREDICTION_INTERVAL_SECONDS)