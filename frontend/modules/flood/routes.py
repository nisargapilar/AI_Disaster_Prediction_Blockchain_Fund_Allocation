from fastapi import APIRouter
from sqlalchemy import select
from datetime import datetime, timezone

from db import async_session
from models import EventModel, PredictionModel

from modules.flood.prediction import predict_flood

router = APIRouter(
prefix="/flood",
tags=["Flood"],
)

# ============================================================

# SERIALIZE FLOOD EVENT

# ============================================================

def serialize_event(row):
return {
"event_id": str(row.event_id),
"disaster_type": row.disaster_type,
"source": row.source,
"event_time": row.event_time.isoformat(),
"location": {
"lat": row.lat,
"lon": row.lon,
"region": row.region,
},
"input_data": row.input_data,
"risk_score": row.risk_score,
"severity_tier": row.severity_tier,
"fund_status": row.fund_status,
}

# ============================================================

# SERIALIZE FLOOD PREDICTION

# ============================================================

def serialize_prediction(row):
return {
"prediction_id": str(row.prediction_id),
"disaster_type": row.disaster_type,
"region": row.region,
"predicted_time": row.predicted_time.isoformat(),
"input_data": row.input_data,
"risk_score": row.risk_score,
"severity_tier": row.severity_tier,
"matched_event_id": (
str(row.matched_event_id)
if row.matched_event_id
else None
),
"is_simulated": row.is_simulated,
"created_at": (
row.created_at.isoformat()
if row.created_at
else None
),
}

# ============================================================

# GET DETECTED FLOOD EVENTS

# ============================================================

@router.get(
"/detected-flood-events",
summary="Detected Flood Events",
)
async def get_detected_flood_events():

```
async with async_session() as session:

    result = await session.execute(
        select(EventModel)
        .where(
            EventModel.disaster_type == "flood",
            EventModel.source == "real",
        )
        .order_by(
            EventModel.event_time.desc()
        )
        .limit(50)
    )

    return [
        serialize_event(row)
        for row in result.scalars().all()
    ]
```

# ============================================================

# GET PREDICTED FLOOD EVENTS

# ============================================================

@router.get(
"/predicted-flood-events",
summary="Predicted Flood Events",
)
async def get_predicted_flood_events():

```
async with async_session() as session:

    result = await session.execute(
        select(PredictionModel)
        .where(
            PredictionModel.disaster_type == "flood"
        )
        .order_by(
            PredictionModel.predicted_time.desc()
        )
        .limit(50)
    )

    return [
        serialize_prediction(row)
        for row in result.scalars().all()
    ]
```

# ============================================================

# SIMULATE FLOOD DETECTION

# ============================================================

@router.post(
"/simulate-detection",
summary="Simulate Flood Detection",
)
async def simulate_detection():

```
return {
    "message": "Flood detection simulation endpoint",
    "disaster_type": "flood",
    "status": "success",
}
```

# ============================================================

# SIMULATE FLOOD PREDICTION

# ============================================================

@router.post(
"/simulate-prediction",
summary="Simulate Flood Prediction",
)
async def simulate_prediction(
rainfall: float,
humidity: float,
temperature: float,
lat: float,
lon: float,
region: str,
):

```
# --------------------------------------------------------
# Calculate rainfall score
# --------------------------------------------------------

rainfall_score = min(
    max(rainfall, 0.0) / 10.0,
    1.0,
)

# --------------------------------------------------------
# Calculate humidity score
# --------------------------------------------------------

humidity_score = min(
    max(humidity, 0.0) / 100.0,
    1.0,
)

# --------------------------------------------------------
# Calculate temperature score
# --------------------------------------------------------

if temperature <= 25:
    temperature_score = 1.0

elif temperature <= 30:
    temperature_score = 0.7

else:
    temperature_score = 0.4

# --------------------------------------------------------
# Calculate flood probability
# --------------------------------------------------------

probability = (
    rainfall_score * 0.60
    + humidity_score * 0.25
    + temperature_score * 0.15
)

probability = max(
    0.0,
    min(probability, 1.0),
)

# --------------------------------------------------------
# Calculate severity
# --------------------------------------------------------

if probability >= 0.90:
    severity = "critical"
    risk_score = 0.95

elif probability >= 0.70:
    severity = "high"
    risk_score = 0.75

elif probability >= 0.40:
    severity = "medium"
    risk_score = 0.50

else:
    severity = "low"
    risk_score = 0.20

# --------------------------------------------------------
# Create prediction
# --------------------------------------------------------

now = datetime.now(timezone.utc)

prediction = PredictionModel(
    disaster_type="flood",
    region=region,
    predicted_time=now,

    input_data={
        "rainfall": rainfall,
        "humidity": humidity,
        "temperature": temperature,
        "latitude": lat,
        "longitude": lon,
        "probability": round(probability, 2),
        "sequence_length": 1,
        "based_on_event_ids": [],
    },

    risk_score=risk_score,
    severity_tier=severity,

    matched_event_id=None,

    is_simulated=True,

    created_at=now,
)

# --------------------------------------------------------
# Save prediction to database
# --------------------------------------------------------

async with async_session() as session:

    try:

        session.add(prediction)

        await session.commit()

        await session.refresh(prediction)

        return serialize_prediction(prediction)

    except Exception:

        await session.rollback()

        raise

