# modules/cyclone/detection.py

import httpx
import asyncio
import uuid

from datetime import datetime, timezone

from db import async_session
from models import EventModel

from modules.cyclone.config import (
    WEATHER_API_URL,
    WEATHER_API_KEY,
    POLL_INTERVAL_SECONDS,
    CYCLONE_MONITOR_LOCATIONS
)


async def fetch_weather(lat, lon):
    """
    Fetch real weather data from OpenWeather API.
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

        return response.json()



def detect_cyclone(wind_speed, pressure):
    """
    Calculate cyclone risk based on wind speed and pressure.
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


    # Determine severity
    if risk_score >= 80:
        severity = "critical"
    elif risk_score >= 50:
        severity = "high"
    elif risk_score >= 30:
        severity = "medium"
    else:
        severity = "low"

    return {
        "risk_score": risk_score / 100,
        "severity_tier": severity
    }


async def fetch_and_process():
    """
    Monitor all configured cyclone-prone locations
    and save real cyclone events into database.
    """

    print("Checking cyclone data...")

    results = []


    for location in CYCLONE_MONITOR_LOCATIONS:

        try:

            weather = await fetch_weather(
                location["lat"],
                location["lon"]
            )


            # Convert m/s to km/h
            wind_speed = weather["wind"]["speed"] * 3.6

            pressure = weather["main"]["pressure"]


            result = detect_cyclone(
                wind_speed,
                pressure
            )


            cyclone_result = {

                "disaster_type": "cyclone",

                "source": "real",

                "state": location["state"],

                "region": location["region"],

                "latitude": location["lat"],

                "longitude": location["lon"],

                "wind_speed": wind_speed,

                "pressure": pressure,

                "risk_score": result["risk_score"],

                "severity_tier": result["severity_tier"]

            }


            print(
                "Cyclone result:",
                cyclone_result
            )


            # -------------------------------
            # SAVE REAL EVENT TO DATABASE
            # -------------------------------

            row = EventModel(

                disaster_type="cyclone",

                source="real",

                external_id=f"openweather_{uuid.uuid4()}",

                event_time=datetime.now(timezone.utc),

                lat=location["lat"],

                lon=location["lon"],

                region=location["region"],

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

                )
            )


            async with async_session() as session:

                session.add(row)

                await session.commit()



            results.append(cyclone_result)



        except Exception as e:

            print(
                f"Error checking {location['region']}:",
                e
            )


    return results




async def start_polling():
    """
    Poll weather data every configured interval.
    """

    print("Cyclone polling started")


    while True:

        try:

            await fetch_and_process()


        except Exception as e:

            print(
                "Cyclone poll error:",
                e
            )


        await asyncio.sleep(
            POLL_INTERVAL_SECONDS
        )