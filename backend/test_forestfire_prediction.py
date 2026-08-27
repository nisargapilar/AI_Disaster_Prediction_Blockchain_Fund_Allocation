import asyncio

from datetime import datetime, timezone

from modules.forest_fire.prediction import predict_event
from models import EventModel


# ============================================================
# TEST FOREST FIRE ML PREDICTION
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("TESTING FOREST FIRE ML PREDICTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Create a sample forest fire event
    # --------------------------------------------------------

    event = EventModel(

        disaster_type="forest_fire",

        source="real",

        external_id="test_prediction_001",

        event_time=datetime.now(
            timezone.utc
        ),

        lat=22.5,

        lon=78.9,

        region="Test Region",

        input_data={

            # ML features
            "brightness": 340.0,

            "scan": 1.2,

            "track": 1.1,

            "confidence": 80.0,

            "bright_t31": 295.0,

            "daynight": "D",

            "type": 0,

            # Additional FIRMS information
            "frp": 25.0,

            "satellite": "N",

            "instrument": "VIIRS"

        },

        risk_score=0.0,

        severity_tier="low",

        fund_status="not_applicable"
    )


    # --------------------------------------------------------
    # Run prediction
    # --------------------------------------------------------

    print("\nRunning XGBoost prediction...")

    result = predict_event(event)


    # --------------------------------------------------------
    # Display result
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("PREDICTION RESULT")
    print("=" * 60)

    print(
        "\nPredicted severity :",
        result["severity_tier"]
    )

    print(
        "Risk score         :",
        f"{result['risk_score']:.2f}"
    )

    print(
        "Model confidence   :",
        f"{result['model_confidence']:.4f}"
    )


    # --------------------------------------------------------
    # Class probabilities
    # --------------------------------------------------------

    print("\nClass probabilities:")

    for class_name, probability in (
        result["class_probabilities"].items()
    ):

        print(
            f"  {class_name:>6} : "
            f"{probability:.4f}"
        )


    # --------------------------------------------------------
    # Features used by model
    # --------------------------------------------------------

    print("\nML Features Used:")

    for feature, value in result["features"].items():

        print(
            f"  {feature:20} : {value}"
        )


    print("\n" + "=" * 60)
    print("FOREST FIRE ML PREDICTION TEST SUCCESSFUL")
    print("=" * 60)


if __name__ == "__main__":

    main()