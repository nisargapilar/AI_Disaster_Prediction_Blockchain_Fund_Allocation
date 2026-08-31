
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import uuid

from sqlalchemy import select

from db import async_session
from models import EventModel, PredictionModel

from .detection import detect_cyclone
from .prediction import (
    predict_cyclone,
    create_feature_row,
    location_history,
    SEQUENCE_LENGTH,
)


router = APIRouter(
    prefix="/cyclone",
    tags=["Cyclone"]
)


# ============================================================
# SERIALIZE EVENT
# ============================================================

def serialize_event(row: EventModel):
    return {
        "event_id": str(row.event_id),
        "disaster_type": row.disaster_type,
        "source": row.source,
        "external_id": row.external_id,
        "event_time": row.event_time.isoformat(),
        "location": {
            "lat": row.lat,
            "lon": row.lon,
            "region": row.region
        },
        "input_data": row.input_data,
        "risk_score": row.risk_score,
        "severity_tier": row.severity_tier,
        "fund_status": row.fund_status,
    }


# ============================================================
# SERIALIZE PREDICTION
# ============================================================

def serialize_prediction(row: PredictionModel):
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
# 1. GET DETECTED CYCLONE EVENTS
#
# GET /cyclone/detected-cyclone-events
# ============================================================

@router.get("/detected-cyclone-events")
async def get_detected_cyclone_events():

    async with async_session() as session:

        result = await session.execute(
            select(EventModel)
            .where(
                EventModel.disaster_type == "cyclone"
            )
            .order_by(
                EventModel.event_time.desc()
            )
            .limit(100)
        )

        rows = result.scalars().all()

    return [
        serialize_event(row)
        for row in rows
    ]


# ============================================================
# 2. POST SIMULATE DETECTION
#
# POST /cyclone/simulate-detection
# ============================================================

@router.post("/simulate-detection")
async def simulate_detection(
    wind_speed: float,
    pressure: float,
    lat: float,
    lon: float,
    region: str = "Simulated Region"
):

    result = detect_cyclone(
        wind_speed,
        pressure
    )

    row = EventModel(
        disaster_type="cyclone",

        source="simulated",

        external_id=(
            f"cyclone_{uuid.uuid4()}"
        ),

        event_time=datetime.now(
            timezone.utc
        ),

        lat=lat,

        lon=lon,

        region=region,

        input_data={
            "wind_speed": wind_speed,
            "pressure": pressure
        },

        risk_score=result["risk_score"],

        severity_tier=result["severity_tier"],

        fund_status=(
            "pending"
            if result["severity_tier"]
            in ["high", "critical"]
            else "not_applicable"
        ),

        created_at=datetime.now(
            timezone.utc
        ),
    )

    async with async_session() as session:

        session.add(row)

        await session.commit()

        await session.refresh(row)

    return serialize_event(row)


# ============================================================
# 3. GET PREDICTED CYCLONE EVENTS
#
# GET /cyclone/predicted-cyclone-events
# ============================================================

@router.get("/predicted-cyclone-events")
async def get_predicted_cyclone_events():

    async with async_session() as session:

        result = await session.execute(
            select(PredictionModel)
            .where(
                PredictionModel.disaster_type
                == "cyclone"
            )
            .order_by(
                PredictionModel.predicted_time.desc()
            )
            .limit(100)
        )

        rows = result.scalars().all()

    return [
        serialize_prediction(row)
        for row in rows
    ]


# ============================================================
# 4. POST SIMULATE PREDICTION
#
# POST /cyclone/simulate-prediction
# ============================================================

@router.post("/simulate-prediction")
async def simulate_prediction(
    wind_speed: float,
    pressure: float,
    lat: float,
    lon: float,
    region: str = "Simulated Region",
    storm_speed: float = 0.0,
    storm_dir: float = 0.0,
    dist2land: float = 0.0,
):

    location = {
        "lat": lat,
        "lon": lon,
        "region": region,
        "storm_speed": storm_speed,
        "dist2land": dist2land,
    }

    # --------------------------------------------------------
    # Create simulated weather data
    # --------------------------------------------------------

    weather = {
        "wind": {
            "speed": wind_speed / 3.6,
            "deg": storm_dir,
        },

        "main": {
            "pressure": pressure,
        },
    }

    # --------------------------------------------------------
    # Create history key
    # --------------------------------------------------------

    history_key = f"{lat}_{lon}"

    if history_key not in location_history:
        location_history[history_key] = []

    history = location_history[history_key]

    # --------------------------------------------------------
    # Previous wind
    # --------------------------------------------------------

    previous_wind = None

    if history:
        previous_wind = history[-1]["WMO_WIND"]

    # --------------------------------------------------------
    # Create feature row
    # --------------------------------------------------------

    feature_row = create_feature_row(
        weather,
        location,
        previous_wind
    )

    # --------------------------------------------------------
    # Add observation
    # --------------------------------------------------------

    history.append(feature_row)

    # --------------------------------------------------------
    # Keep only required observations
    # --------------------------------------------------------

    if len(history) > SEQUENCE_LENGTH:
        del history[:-SEQUENCE_LENGTH]

    # --------------------------------------------------------
    # CNN-LSTM requires 12 observations
    # --------------------------------------------------------

    if len(history) < SEQUENCE_LENGTH:

        return {
            "status": "collecting_data",

            "message": (
                "CNN-LSTM requires "
                f"{SEQUENCE_LENGTH} observations."
            ),

            "observations_collected": len(history),

            "observations_required": SEQUENCE_LENGTH,

            "region": region,
        }

    # --------------------------------------------------------
    # Run CNN-LSTM prediction
    # --------------------------------------------------------

    prediction = predict_cyclone(
        history
    )

    if prediction is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "Cyclone prediction "
                "could not be generated."
            )
        )

    # --------------------------------------------------------
    # Save prediction
    # --------------------------------------------------------

    row = PredictionModel(

        disaster_type="cyclone",

        region=region,

        predicted_time=datetime.now(
            timezone.utc
        ),

        input_data={

            "features": feature_row,

            "prediction_probability":
                prediction[
                    "prediction_probability"
                ],

            "predicted_intensification":
                prediction[
                    "predicted_intensification"
                ],
        },

        risk_score=prediction[
            "risk_score"
        ],

        severity_tier=prediction[
            "severity_tier"
        ],

        matched_event_id=None,

        is_simulated=True,

    )

    async with async_session() as session:

        session.add(row)

        await session.commit()

        await session.refresh(row)

    return serialize_prediction(row)
