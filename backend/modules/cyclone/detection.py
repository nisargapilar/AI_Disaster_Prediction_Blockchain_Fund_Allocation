# modules/cyclone/detection.py

import httpx
import asyncio
from datetime import datetime, timezone

from modules.cyclone.config import (
    WEATHER_API_URL,
    WEATHER_API_KEY,
    POLL_INTERVAL_SECONDS
)


async def fetch_weather(lat, lon):
    """
    Fetch real weather data from OpenWeather API
    """

    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    async with httpx.AsyncClient() as client:

        response = await client.get(
            WEATHER_API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    return data



def detect_cyclone(
        wind_speed,
        pressure,
        lat,
        lon
):
    """
    Calculate cyclone risk
    """

    risk_score = 0


    # Wind speed calculation
    if wind_speed >= 120:
        risk_score += 50

    elif wind_speed >= 80:
        risk_score += 30


    # Pressure calculation
    if pressure <= 980:
        risk_score += 50

    elif pressure <= 1000:
        risk_score += 30



    # Severity

    if risk_score >= 80:
        severity = "critical"

    elif risk_score >= 50:
        severity = "high"

    elif risk_score >= 30:
        severity = "medium"

    else:
        severity = "low"



    return {
        "disaster_type": "cyclone",
        "source": "real",

        "latitude": lat,
        "longitude": lon,

        "wind_speed": wind_speed,
        "pressure": pressure,

        "risk_score": risk_score,
        "severity_tier": severity,

        "event_time": datetime.now(timezone.utc)
    }



async def fetch_and_process():

    print("Checking cyclone data...")


    # Location to monitor
    lat = 13.08
    lon = 80.27


    # 1. Get weather
    weather = await fetch_weather(
        lat,
        lon
    )


    # 2. Extract values

    wind_speed = weather["wind"]["speed"]

    pressure = weather["main"]["pressure"]


    # 3. Detect cyclone

    cyclone_result = detect_cyclone(
        wind_speed,
        pressure,
        lat,
        lon
    )


    print(
        "Cyclone result:",
        cyclone_result
    )


    # Database saving will be added here


    return cyclone_result



async def start_polling():

    print("Cyclone polling started")


    while True:

        try:

            await fetch_and_process()


        except Exception as e:

            print(
                "Cyclone poll error:",
                e
            )


        # 1 hour
        await asyncio.sleep(
            POLL_INTERVAL_SECONDS
        )