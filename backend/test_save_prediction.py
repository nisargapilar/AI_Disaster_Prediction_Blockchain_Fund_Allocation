import asyncio

from sqlalchemy import select

from db import async_session
from models import EventModel

from modules.forest_fire.prediction import save_prediction


async def main():

    print("\n" + "=" * 60)
    print("TESTING DATABASE FOREST FIRE PREDICTION")
    print("=" * 60)

    # ========================================================
    # 1. FIND LATEST FOREST FIRE EVENT
    # ========================================================

    async with async_session() as session:

        result = await session.execute(

            select(EventModel)
            .where(
                EventModel.disaster_type == "forest_fire"
            )
            .order_by(
                EventModel.created_at.desc()
            )
            .limit(1)

        )

        event = result.scalars().first()

    # ========================================================
    # 2. CHECK WHETHER EVENT EXISTS
    # ========================================================

    if event is None:

        print("\nERROR: No forest fire event found.")

        print(
            "\nThe prediction module is working, "
            "but there is no forest fire event in PostgreSQL."
        )

        print(
            "\nNext we will test NASA FIRMS detection."
        )

        return

    # ========================================================
    # 3. DISPLAY EVENT
    # ========================================================

    print("\nForest fire event found!")

    print(
        "Event ID:",
        event.event_id
    )

    print(
        "Region:",
        event.region
    )

    print(
        "Event time:",
        event.event_time
    )

    print(
        "Severity before ML:",
        event.severity_tier
    )

    # ========================================================
    # 4. RUN ML + SAVE PREDICTION
    # ========================================================

    print("\nRunning prediction and saving to database...")

    prediction = await save_prediction(event)

    # ========================================================
    # 5. DISPLAY RESULT
    # ========================================================

    if prediction:

        print("\n" + "=" * 60)
        print("DATABASE PREDICTION SUCCESSFUL")
        print("=" * 60)

        print(
            "\nPrediction ID:",
            prediction.prediction_id
        )

        print(
            "Disaster type:",
            prediction.disaster_type
        )

        print(
            "Severity:",
            prediction.severity_tier
        )

        print(
            "Risk score:",
            prediction.risk_score
        )

        print(
            "Matched event ID:",
            prediction.matched_event_id
        )

        print(
            "Is simulated:",
            prediction.is_simulated
        )

        print("\n" + "=" * 60)


if __name__ == "__main__":

    asyncio.run(main())