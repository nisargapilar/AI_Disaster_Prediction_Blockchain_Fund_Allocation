import asyncio

from sqlalchemy import select

from db import async_session
from models import EventModel

from modules.forest_fire.prediction import (
    predict_event
)


async def main():

    print(
        "\n=================================================="
    )

    print(
        "FOREST FIRE PREDICTION TEST"
    )

    print(
        "=================================================="
    )


    async with async_session() as session:

        result = await session.execute(

            select(
                EventModel
            )
            .where(
                EventModel.disaster_type
                == "forest_fire"
            )
            .order_by(
                EventModel.created_at.desc()
            )
            .limit(1)

        )


        event = (
            result.scalars().first()
        )


    if event is None:

        print(
            "\n❌ No forest fire event found."
        )

        print(
            "First run your FIRMS detection."
        )

        return


    print(
        "\nEvent found:"
    )

    print(
        "Event ID:",
        event.event_id
    )

    print(
        "Location:",
        event.region
    )


    # ========================================================
    # RUN MODEL
    # ========================================================

    result = predict_event(
        event
    )


    print(
        "\n=================================================="
    )

    print(
        "PREDICTION RESULT"
    )

    print(
        "=================================================="
    )


    print(
        "\nSeverity:",
        result[
            "severity_tier"
        ]
    )


    print(
        "Risk score:",
        f"{result['risk_score']:.2f}"
    )


    print(
        "Model confidence:",
        f"{result['model_confidence']:.4f}"
    )


    print(
        "\nClass probabilities:"
    )


    for class_name, probability in (
        result[
            "class_probabilities"
        ].items()
    ):

        print(
            f"  {class_name}: "
            f"{probability:.4f}"
        )


    print(
        "\nML Features:"
    )


    for feature, value in (
        result[
            "features"
        ].items()
    ):

        print(
            f"  {feature}: {value}"
        )


    print(
        "\n=================================================="
    )

    print(
        "✅ PREDICTION TEST SUCCESSFUL"
    )

    print(
        "=================================================="
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )