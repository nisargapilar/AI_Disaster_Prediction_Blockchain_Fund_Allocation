from fastapi import APIRouter
from sqlalchemy import select

from db import async_session
from models import EventModel, PredictionModel

from modules.flood.prediction import predict_event


router = APIRouter(
    prefix="/flood",
    tags=["Flood"],
)


# ============================================================
# SERIALIZE DETECTED FLOOD EVENT
# ============================================================

def serialize_event(row):

    return {
        "event_id": str(
            row.event_id
        ),

        "disaster_type": row.disaster_type,

        "source": row.source,

        "event_time": (
            row.event_time.isoformat()
            if row.event_time
            else None
        ),

        "location": {
            "lat": row.lat,
            "lon": row.lon,
            "region": row.region,
        },

        "input_data": (
            row.input_data
            or {}
        ),

        "risk_score": row.risk_score,

        "severity_tier": (
            row.severity_tier
        ),

        "fund_status": (
            row.fund_status
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

    async with async_session() as session:

        result = await session.execute(

            select(EventModel)

            .where(
                EventModel.disaster_type == "flood",

                EventModel.source != "prediction",
            )

            .order_by(
                EventModel.event_time.desc()
            )

            .limit(50)
        )

        rows = result.scalars().all()

        return [
            serialize_event(row)
            for row in rows
        ]


# ============================================================
# SERIALIZE FLOOD PREDICTION
# ============================================================

def serialize_prediction(row):

    probability = 0.0

    if row.input_data:

        probability = row.input_data.get(
            "probability",
            0.0,
        )

    return {

        "prediction_id": str(
            row.prediction_id
        ),

        "disaster_type": (
            row.disaster_type
        ),

        "region": row.region,

        "predicted_time": (
            row.predicted_time.isoformat()
            if row.predicted_time
            else None
        ),

        "input_data": (
            row.input_data
            or {}
        ),

        "risk_score": (
            row.risk_score
        ),

        "severity_tier": (
            row.severity_tier
        ),

        "matched_event_id": (
            str(row.matched_event_id)
            if row.matched_event_id
            else None
        ),

        "is_simulated": (
            row.is_simulated
        ),

        # Convenient field for frontend
        "probability": probability,
    }


# ============================================================
# GET PREDICTED FLOOD EVENTS
# ============================================================

@router.get(
    "/predicted-flood-events",
    summary="Predicted Flood Events",
)
async def get_predicted_flood_events():

    async with async_session() as session:

        result = await session.execute(

            select(PredictionModel)

            .where(
                PredictionModel.disaster_type
                == "flood"
            )

            .order_by(
                PredictionModel.predicted_time.desc()
            )

            .limit(50)
        )

        rows = result.scalars().all()

        return [
            serialize_prediction(row)
            for row in rows
        ]


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

    # --------------------------------------------------------
    # CREATE PREDICTION
    # --------------------------------------------------------

    prediction = await predict_event(

        rainfall=rainfall,

        humidity=humidity,

        temperature=temperature,

        lat=lat,

        lon=lon,

        region=region,

        is_simulated=True,
    )

    # --------------------------------------------------------
    # GET PROBABILITY
    # --------------------------------------------------------

    probability = 0.0

    if prediction.input_data:

        probability = prediction.input_data.get(
            "probability",
            0.0,
        )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {

        "prediction_id": str(
            prediction.prediction_id
        ),

        "disaster_type": (
            prediction.disaster_type
        ),

        "region": (
            prediction.region
        ),

        "predicted_time": (
            prediction.predicted_time.isoformat()
            if prediction.predicted_time
            else None
        ),

        "flood_probability": probability,

        "risk_score": (
            prediction.risk_score
        ),

        "severity_tier": (
            prediction.severity_tier
        ),

        "matched_event_id": (
            str(prediction.matched_event_id)
            if prediction.matched_event_id
            else None
        ),

        "is_simulated": (
            prediction.is_simulated
        ),

        "model": (
            "rule_based_flood_model"
        ),

        "features": {

            "rainfall": rainfall,

            "humidity": humidity,

            "temperature": temperature,

            "latitude": lat,

            "longitude": lon,

            "region": region,
        },
    }


# ============================================================
# SIMULATE FLOOD DETECTION
# ============================================================

@router.post(
    "/simulate-detection",
    summary="Simulate Flood Detection",
)
async def simulate_detection():

    return {

        "message": (
            "Flood detection simulation endpoint"
        ),

        "disaster_type": "flood",

        "status": "success",
    }