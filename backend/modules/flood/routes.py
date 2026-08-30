from fastapi import APIRouter
from sqlalchemy import select
from datetime import datetime, timezone

from db import async_session
from models import EventModel

from modules.flood.prediction import predict_event


router = APIRouter(
    prefix="/flood",
    tags=["Flood"],
)


# ============================================================
# SERIALIZE EVENT
# ============================================================

def serialize(row):
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
# GET DETECTED FLOOD EVENTS
# ============================================================

@router.get(
    "/detected-flood-events",
    summary="Detected Flood Events"
)
async def get_detected_flood_events():

    async with async_session() as session:

        result = await session.execute(

            select(EventModel)
            .where(
                EventModel.disaster_type == "flood",
                EventModel.source != "prediction"
            )
            .order_by(
                EventModel.event_time.desc()
            )
            .limit(50)

        )

        return [
            serialize(row)
            for row in result.scalars().all()
        ]


# ============================================================
# SIMULATE FLOOD DETECTION
# ============================================================

@router.post(
    "/simulate-detection",
    summary="Simulate Detection"
)
async def simulate_detection():

    return {
        "message": "Flood detection simulation endpoint",
        "disaster_type": "flood",
        "status": "success"
    }


# ============================================================
# GET PREDICTED FLOOD EVENTS
# ============================================================

@router.get(
    "/predicted-flood-events",
    summary="Predicted Flood Events"
)
async def get_predicted_flood_events():

    async with async_session() as session:

        result = await session.execute(

            select(EventModel)
            .where(
                EventModel.disaster_type == "flood",
                EventModel.source == "prediction"
            )
            .order_by(
                EventModel.event_time.desc()
            )
            .limit(50)

        )

        return [
            serialize(row)
            for row in result.scalars().all()
        ]


# ============================================================
# SIMULATE FLOOD PREDICTION
# ============================================================

@router.post(
    "/simulate-prediction",
    summary="Simulate Prediction"
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
    # Create temporary event for prediction
    # --------------------------------------------------------

    event = EventModel(

        disaster_type="flood",

        source="prediction",

        event_time=datetime.now(
            timezone.utc
        ),

        lat=lat,

        lon=lon,

        region=region,

        input_data={

            "MonsoonIntensity": rainfall,

            "TopographyDrainage": 0.0,
            "RiverManagement": 0.0,
            "Deforestation": 0.0,
            "Urbanization": 0.0,
            "ClimateChange": 0.0,
            "DamsQuality": 0.0,
            "Siltation": 0.0,
            "AgriculturalPractices": 0.0,
            "Encroachments": 0.0,
            "IneffectiveDisasterPreparedness": 0.0,
            "DrainageSystems": 0.0,
            "CoastalVulnerability": 0.0,
            "Landslides": 0.0,
            "Watersheds": 0.0,
            "DeterioratingInfrastructure": 0.0,
            "PopulationScore": 0.0,
            "WetlandLoss": 0.0,
            "InadequatePlanning": 0.0,
            "PoliticalFactors": 0.0,

            "rainfall": rainfall,
            "humidity": humidity,
            "temperature": temperature,
            "lat": lat,
            "lon": lon,

        },

    )

    # --------------------------------------------------------
    # RUN FLOOD LSTM
    # --------------------------------------------------------

    result = predict_event(event)

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {

        "disaster_type": "flood",

        "region": region,

        "latitude": lat,

        "longitude": lon,

        "flood_probability":
            result["flood_probability"],

        "risk_score":
            result["risk_score"],

        "severity_tier":
            result["severity_tier"],

        "model": "LSTM",

        "features":
            result["features"],

    }