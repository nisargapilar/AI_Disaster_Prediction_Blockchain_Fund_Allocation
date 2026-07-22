from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

from db import async_session
from models import EventModel

from .detection import detect_cyclone, fetch_weather


router = APIRouter(
    prefix="/cyclone",
    tags=["Cyclone Detection"]
)


def serialize(row: EventModel):
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


# --------------------------------------------------
# REAL DETECTION (OpenWeather API)
# GET /cyclone/detect
# --------------------------------------------------
@router.get("/detect")
async def detect(
    lat: float,
    lon: float
):

    weather = await fetch_weather(lat, lon)

    wind_speed = weather["wind"]["speed"]
    pressure = weather["main"]["pressure"]

    result = detect_cyclone(
        wind_speed,
        pressure
    )

    row = EventModel(
        disaster_type="cyclone",
        source="real",

        external_id=f"openweather_{uuid.uuid4()}",
        event_time=datetime.now(timezone.utc),

        # Coordinates returned by OpenWeather
        lat=weather["coord"]["lat"],
        lon=weather["coord"]["lon"],

        # City name returned by OpenWeather
        region=weather.get("name", "Unknown"),

        input_data={
            "wind_speed": wind_speed,
            "pressure": pressure
        },

        risk_score=result["risk_score"],
        severity_tier=result["severity_tier"],

        fund_status=(
            "pending"
            if result["severity_tier"] in ["high", "critical"]
            else "not_applicable"
        ),
        created_at=datetime.now(timezone.utc),

    )

    async with async_session() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)

    return serialize(row)


# --------------------------------------------------
# SIMULATION
# POST /cyclone/simulate
# --------------------------------------------------
@router.post("/simulate")
async def simulate(
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

        external_id=f"cyclone_{uuid.uuid4()}",
        event_time=datetime.now(timezone.utc),

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
            if result["severity_tier"] in ["high", "critical"]
            else "not_applicable"
        ),
                created_at=datetime.now(timezone.utc),

    )

    async with async_session() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)

    return serialize(row)