import asyncio

from sqlalchemy import select

from db import async_session
from models import EventModel, PredictionModel


async def main():

    print("=" * 60)
    print("FOREST FIRE DATABASE VERIFICATION")
    print("=" * 60)

    async with async_session() as session:

        # ====================================================
        # 1. GET LATEST FOREST FIRE EVENTS
        # ====================================================

        result = await session.execute(

            select(EventModel)
            .where(
                EventModel.disaster_type == "forest_fire"
            )
            .order_by(
                EventModel.created_at.desc()
            )
            .limit(10)

        )

        events = result.scalars().all()

        print(
            f"\nForest fire events found: {len(events)}"
        )

        if not events:

            print("\nNO FOREST FIRE EVENTS FOUND.")
            return

        # ====================================================
        # 2. DISPLAY EVENTS
        # ====================================================

        print("\n" + "=" * 60)
        print("LATEST FOREST FIRE EVENTS")
        print("=" * 60)

        for index, event in enumerate(
            events,
            start=1
        ):

            print(f"\nEvent {index}")
            print("-" * 40)

            print(
                "Event ID      :",
                event.event_id
            )

            print(
                "Source        :",
                event.source
            )

            print(
                "Latitude      :",
                event.lat
            )

            print(
                "Longitude     :",
                event.lon
            )

            print(
                "Region        :",
                event.region
            )

            print(
                "Severity      :",
                event.severity_tier
            )

            print(
                "Risk Score    :",
                event.risk_score
            )

            print(
                "Event Time    :",
                event.event_time
            )

            print(
                "Created At    :",
                event.created_at
            )

            print(
                "Input Data    :",
                event.input_data
            )

        # ====================================================
        # 3. GET PREDICTIONS
        # ====================================================

        prediction_result = await session.execute(

            select(PredictionModel)
            .order_by(
                PredictionModel.created_at.desc()
            )
            .limit(10)

        )

        predictions = (
            prediction_result
            .scalars()
            .all()
        )

        print("\n" + "=" * 60)
        print("LATEST PREDICTIONS")
        print("=" * 60)

        print(
            f"\nPredictions found: {len(predictions)}"
        )

        for index, prediction in enumerate(
            predictions,
            start=1
        ):

            print(f"\nPrediction {index}")
            print("-" * 40)

            print(
                "Prediction ID :",
                prediction.prediction_id
            )

            print(
                "Disaster Type :",
                prediction.disaster_type
            )

            print(
                "Severity      :",
                prediction.severity_tier
            )

            print(
                "Risk Score    :",
                prediction.risk_score
            )

            print(
                "Matched Event :",
                prediction.matched_event_id
            )

            print(
                "Simulated     :",
                prediction.is_simulated
            )

            print(
                "Created At    :",
                prediction.created_at
            )


if __name__ == "__main__":

    asyncio.run(main())