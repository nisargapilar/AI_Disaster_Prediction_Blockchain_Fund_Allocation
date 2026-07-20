from datetime import datetime, timezone
import asyncio
import traceback

import httpx

from db import async_session
from models import EventModel

from modules.flood.severity import (
    compute_severity,
    is_fund_eligible,
)

from modules.flood.config import POLL_INTERVAL_SECONDS


# Locations to monitor
LOCATIONS = [
    {"region": "Assam (Guwahati)", "lat": 26.14, "lon": 91.74},
    {"region": "Patna", "lat": 25.59, "lon": 85.14},
    {"region": "Kochi", "lat": 9.93, "lon": 76.27},
    {"region": "Chennai", "lat": 13.08, "lon": 80.27},
    {"region": "Mumbai", "lat": 19.07, "lon": 72.88},
]


async def predict_flood(
    rainfall: float,
    humidity: float,
    temperature: float,
    lat: float,
    lon: float,
    region: str,
):
    # Normalize weather parameters
    rainfall_score = min(rainfall / 10.0, 1.0)
    humidity_score = humidity / 100.0

    # Cooler temperatures increase flood persistence
    if temperature <= 25:
        temperature_score = 1.0
    elif temperature <= 30:
        temperature_score = 0.7
    else:
        temperature_score = 0.4

    # Flood probability
    probability = (
        rainfall_score * 0.60
        + humidity_score * 0.25
        + temperature_score * 0.15
    )

    probability = min(probability, 1.0)

    # Severity
    tier, score = compute_severity(probability)

    row = EventModel(
    disaster_type="flood",
    source="real",
    external_id=None,
    event_time=datetime.now(timezone.utc),
    lat=lat,
    lon=lon,
    region=region,
    input_data={
        "rainfall": rainfall,
        "humidity": humidity,
        "temperature": temperature,
        "probability": round(probability, 2),
    },
    risk_score=score,
    severity_tier=tier,

    # Values allowed by your PostgreSQL schema
    fund_status=(
        "pending"
        if is_fund_eligible(tier)
        else "not_applicable"
    ),
        created_at=datetime.now(timezone.utc),

)

    async with async_session() as session:
        try:
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return row

        except Exception:
            await session.rollback()
            print("========== FLOOD ERROR ==========")
            traceback.print_exc()
            print("=================================")
            raise


async def fetch_weather(location):
    """
    Fetch latest weather data from Open-Meteo.
    """

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={location['lat']}"
        f"&longitude={location['lon']}"
        "&hourly=precipitation,temperature_2m,relative_humidity_2m"
    )

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()

    return {
        "rainfall": data["hourly"]["precipitation"][0],
        "temperature": data["hourly"]["temperature_2m"][0],
        "humidity": data["hourly"]["relative_humidity_2m"][0],
        "lat": location["lat"],
        "lon": location["lon"],
        "region": location["region"],
    }


async def start_polling():
    while True:
        print("Flood detection polling running...")

        for location in LOCATIONS:
            try:
                weather = await fetch_weather(location)

                await predict_flood(
                    rainfall=weather["rainfall"],
                    humidity=weather["humidity"],
                    temperature=weather["temperature"],
                    lat=weather["lat"],
                    lon=weather["lon"],
                    region=weather["region"],
                )

                print(
                    f"Processed {weather['region']} | "
                    f"Rain={weather['rainfall']} mm "
                    f"Humidity={weather['humidity']}% "
                    f"Temp={weather['temperature']}°C"
                )

            except Exception:
                print(f"Failed for {location['region']}")
                traceback.print_exc()

        await asyncio.sleep(POLL_INTERVAL_SECONDS)