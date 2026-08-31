from datetime import datetime, timezone
import asyncio
import traceback

import httpx
from sqlalchemy import select

from db import async_session
from models import EventModel, PredictionModel

from modules.flood.severity import (
    compute_severity,
)

from modules.flood.config import (
    POLL_INTERVAL_SECONDS,
    OPEN_METEO_API_URL,
    LOCATIONS,
)


# ============================================================
# FLOOD PREDICTION
# ============================================================

async def predict_event(
    rainfall: float,
    humidity: float,
    temperature: float,
    lat: float,
    lon: float,
    region: str,
    is_simulated: bool = False,
):
    """
    Calculate flood probability and create a record
    in the predictions table.

    IMPORTANT:
    This function does NOT release funds.
    This function does NOT create an EventModel.
    Predictions are stored only in the predictions table.
    """

    # --------------------------------------------------------
    # 1. Normalize rainfall
    # --------------------------------------------------------

    rainfall_score = min(
        max(float(rainfall) / 10.0, 0.0),
        1.0,
    )

    # --------------------------------------------------------
    # 2. Normalize humidity
    # --------------------------------------------------------

    humidity_score = min(
        max(float(humidity) / 100.0, 0.0),
        1.0,
    )

    # --------------------------------------------------------
    # 3. Temperature score
    # --------------------------------------------------------

    if temperature <= 25:
        temperature_score = 1.0

    elif temperature <= 30:
        temperature_score = 0.7

    else:
        temperature_score = 0.4

    # --------------------------------------------------------
    # 4. Calculate flood probability
    # --------------------------------------------------------

    probability = (
        rainfall_score * 0.60
        + humidity_score * 0.25
        + temperature_score * 0.15
    )

    probability = min(
        max(probability, 0.0),
        1.0,
    )

    # --------------------------------------------------------
    # 5. Calculate severity
    # --------------------------------------------------------

    severity_tier, risk_score = compute_severity(
        probability
    )

    # --------------------------------------------------------
    # 6. Try to match an existing flood event
    # --------------------------------------------------------

    matched_event_id = None

    try:
        async with async_session() as session:

            result = await session.execute(
                select(EventModel)
                .where(
                    EventModel.disaster_type == "flood",
                    EventModel.region == region,
                )
                .order_by(
                    EventModel.event_time.desc()
                )
                .limit(1)
            )

            matched_event = result.scalars().first()

            if matched_event:
                matched_event_id = matched_event.event_id

    except Exception:

        print(
            "Warning: Could not find matching flood event."
        )

        traceback.print_exc()

    # --------------------------------------------------------
    # 7. Prediction time
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # 8. Create PredictionModel
    # --------------------------------------------------------

    prediction = PredictionModel(

        disaster_type="flood",

        region=region,

        predicted_time=now,

        input_data={
            "rainfall": float(rainfall),
            "humidity": float(humidity),
            "temperature": float(temperature),

            "latitude": float(lat),
            "longitude": float(lon),

            "probability": round(
                probability,
                4,
            ),

            "model": "rule_based_flood_model",

            "based_on_event_id": (
                str(matched_event_id)
                if matched_event_id
                else None
            ),
        },

        risk_score=float(risk_score),

        severity_tier=severity_tier,

        matched_event_id=matched_event_id,

        is_simulated=is_simulated,
    )

    # --------------------------------------------------------
    # 9. Save prediction
    # --------------------------------------------------------

    async with async_session() as session:

        try:

            session.add(prediction)

            await session.commit()

            await session.refresh(prediction)

            return prediction

        except Exception:

            await session.rollback()

            print(
                "========== FLOOD PREDICTION ERROR =========="
            )

            traceback.print_exc()

            print(
                "============================================="
            )

            raise


# ============================================================
# FETCH CURRENT WEATHER
# ============================================================

async def fetch_weather(location):
    """
    Fetch current weather data from Open-Meteo.
    """

    url = (
        f"{OPEN_METEO_API_URL}"
        f"?latitude={location['lat']}"
        f"&longitude={location['lon']}"
        "&current=precipitation,temperature_2m,"
        "relative_humidity_2m"
    )

    async with httpx.AsyncClient(
        timeout=20
    ) as client:

        response = await client.get(url)

        response.raise_for_status()

        data = response.json()

    current = data["current"]

    return {
        "rainfall": current["precipitation"],
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],

        "lat": location["lat"],
        "lon": location["lon"],
        "region": location["region"],
    }


# ============================================================
# FLOOD PREDICTION POLLING
# ============================================================

async def start_prediction_polling():
    """
    Continuously monitor configured locations
    and create forecast records.

    These records go into the predictions table.
    They do NOT go into the events table.
    """

    while True:

        print(
            "========================================"
        )

        print(
            "Flood prediction polling running..."
        )

        print(
            "========================================"
        )

        for location in LOCATIONS:

            try:

                weather = await fetch_weather(
                    location
                )

                prediction = await predict_event(

                    rainfall=weather["rainfall"],

                    humidity=weather["humidity"],

                    temperature=weather["temperature"],

                    lat=weather["lat"],

                    lon=weather["lon"],

                    region=weather["region"],

                    is_simulated=False,
                )

                probability = (
                    prediction.input_data.get(
                        "probability",
                        0.0,
                    )
                )

                print(
                    f"Predicted {weather['region']} | "
                    f"Rain={weather['rainfall']} mm | "
                    f"Humidity={weather['humidity']}% | "
                    f"Temp={weather['temperature']}°C | "
                    f"Probability={probability} | "
                    f"Severity={prediction.severity_tier} | "
                    f"Risk={prediction.risk_score}"
                )

            except Exception:

                print(
                    f"Failed flood prediction for "
                    f"{location['region']}"
                )

                traceback.print_exc()

        print(
            f"Waiting {POLL_INTERVAL_SECONDS} seconds "
            "before next flood prediction..."
        )

        await asyncio.sleep(
            POLL_INTERVAL_SECONDS
        )