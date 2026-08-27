import asyncio
import json
import joblib

from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

from sqlalchemy import select

from db import async_session
from models import EventModel, PredictionModel

from modules.forest_fire.config import (
    POLL_INTERVAL_SECONDS,
)


# ============================================================
# 1. ARTIFACT PATHS
# ============================================================

# prediction.py
#     ↓
# forest_fire
#     ↓
# modules
#     ↓
# backend
#
# Therefore:
# Path(__file__).resolve().parents[2]
# points to backend/

BACKEND_DIR = Path(
    __file__
).resolve().parents[2]


ARTIFACT_DIR = (
    BACKEND_DIR
    / "ml_artifacts"
    / "forestfire_artifacts"
)


MODEL_PATH = (
    ARTIFACT_DIR
    / "forestfire_xgboost.pkl"
)

IMPUTER_PATH = (
    ARTIFACT_DIR
    / "forestfire_imputer.pkl"
)

LABEL_ENCODER_PATH = (
    ARTIFACT_DIR
    / "forestfire_label_encoder.pkl"
)

FEATURE_REFERENCE_PATH = (
    ARTIFACT_DIR
    / "forestfire_feature_reference.json"
)


# ============================================================
# 2. LOAD ML ARTIFACTS
# ============================================================

print(
    "\n=========================================="
)

print(
    "LOADING FOREST FIRE ML ARTIFACTS"
)

print(
    "=========================================="
)


model = joblib.load(
    MODEL_PATH
)

print(
    "XGBoost model loaded."
)


imputer = joblib.load(
    IMPUTER_PATH
)

print(
    "Imputer loaded."
)


label_encoder = joblib.load(
    LABEL_ENCODER_PATH
)

print(
    "Label encoder loaded."
)


with open(
    FEATURE_REFERENCE_PATH,
    "r"
) as f:

    feature_reference = json.load(f)


FEATURE_COLUMNS = feature_reference[
    "features"
]


print(
    "Feature reference loaded."
)


print(
    "Features:",
    FEATURE_COLUMNS
)


print(
    "Classes:",
    label_encoder.classes_
)


# ============================================================
# 3. SAFE NUMERIC CONVERSION
# ============================================================

def _to_float(
    value,
    default=0.0
):

    try:

        if value is None:
            return default

        return float(value)

    except (
        ValueError,
        TypeError
    ):

        return default


# ============================================================
# 4. GET NUMERIC CONFIDENCE
# ============================================================

def _get_confidence(
    input_data: dict
) -> float:

    value = input_data.get(
        "confidence"
    )

    # Already numeric
    try:

        return float(value)

    except (
        ValueError,
        TypeError
    ):

        pass


    # Original FIRMS confidence
    raw_value = input_data.get(
        "raw_confidence"
    )

    try:

        return float(raw_value)

    except (
        ValueError,
        TypeError
    ):

        pass


    # String fallback
    text = str(
        value or raw_value or ""
    ).strip().lower()


    mapping = {

        "low": 30.0,

        "nominal": 60.0,

        "medium": 60.0,

        "high": 90.0

    }


    return mapping.get(
        text,
        0.0
    )


# ============================================================
# 5. BUILD ML INPUT FROM EVENT
# ============================================================

def _build_feature_dataframe(
    event: EventModel
) -> pd.DataFrame:

    input_data = (
        event.input_data
        or {}
    )


    # --------------------------------------------------------
    # Date features
    #
    # Same logic as training.
    # --------------------------------------------------------

    event_time = event.event_time


    if event_time is None:

        event_time = datetime.now(
            timezone.utc
        )


    month = event_time.month


    day_of_year = (
        event_time.timetuple().tm_yday
    )


    # --------------------------------------------------------
    # Day/night
    # --------------------------------------------------------

    daynight_encoded = input_data.get(
        "daynight_encoded"
    )


    if daynight_encoded is None:

        daynight = str(
            input_data.get(
                "daynight",
                "N"
            )
        ).upper()


        if daynight == "D":

            daynight_encoded = 1

        else:

            daynight_encoded = 0


    # --------------------------------------------------------
    # Type
    # --------------------------------------------------------

    fire_type = input_data.get(
        "type",
        0
    )


    # --------------------------------------------------------
    # Build EXACT training features
    # --------------------------------------------------------

    features = {

        "latitude": _to_float(
            input_data.get(
                "latitude",
                event.lat
            )
        ),

        "longitude": _to_float(
            input_data.get(
                "longitude",
                event.lon
            )
        ),

        "brightness": _to_float(
            input_data.get(
                "brightness"
            )
        ),

        "scan": _to_float(
            input_data.get(
                "scan"
            )
        ),

        "track": _to_float(
            input_data.get(
                "track"
            )
        ),

        "confidence": _get_confidence(
            input_data
        ),

        "bright_t31": _to_float(
            input_data.get(
                "bright_t31"
            )
        ),

        "daynight_encoded": _to_float(
            daynight_encoded
        ),

        "month": _to_float(
            input_data.get(
                "month",
                month
            )
        ),

        "day_of_year": _to_float(
            input_data.get(
                "day_of_year",
                day_of_year
            )
        ),

        "type": _to_float(
            fire_type
        )

    }


    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(
        [features]
    )


    # --------------------------------------------------------
    # CRITICAL:
    # Use EXACT training feature order
    # --------------------------------------------------------

    df = df[
        FEATURE_COLUMNS
    ]


    return df


# ============================================================
# 6. PREDICT ONE FOREST FIRE EVENT
# ============================================================

def predict_event(
    event: EventModel
):

    # --------------------------------------------------------
    # Build features
    # --------------------------------------------------------

    feature_df = (
        _build_feature_dataframe(
            event
        )
    )


    # --------------------------------------------------------
    # Apply SAME fitted imputer
    # --------------------------------------------------------

    feature_array = (
        imputer.transform(
            feature_df
        )
    )


    # --------------------------------------------------------
    # XGBoost prediction
    # --------------------------------------------------------

    prediction = model.predict(
        feature_array
    )


    probabilities = (
        model.predict_proba(
            feature_array
        )
    )


    # --------------------------------------------------------
    # Decode class
    # --------------------------------------------------------

    predicted_class = (
        label_encoder.inverse_transform(
            prediction
        )[0]
    )


    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    model_confidence = float(
        probabilities[0].max()
    )


    # --------------------------------------------------------
    # Risk score
    #
    # 0 - 100
    # --------------------------------------------------------

    risk_score = (
        model_confidence * 100.0
    )


    # --------------------------------------------------------
    # Class probabilities
    # --------------------------------------------------------

    class_probabilities = {}


    for class_name, probability in zip(
        label_encoder.classes_,
        probabilities[0]
    ):

        class_probabilities[
            str(class_name)
        ] = float(
            probability
        )


    return {

        "severity_tier": str(
            predicted_class
        ),

        "risk_score": risk_score,

        "model_confidence": (
            model_confidence
        ),

        "class_probabilities": (
            class_probabilities
        ),

        "features": feature_df.iloc[
            0
        ].to_dict()

    }


# ============================================================
# 7. SAVE PREDICTION TO DATABASE
# ============================================================

async def save_prediction(
    event: EventModel
):

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    result = predict_event(
        event
    )


    # --------------------------------------------------------
    # Check whether prediction already
    # exists for this event.
    #
    # matched_event_id is our link.
    # --------------------------------------------------------

    async with async_session() as session:

        existing_result = await session.execute(

            select(
                PredictionModel
            )
            .where(
                PredictionModel.matched_event_id
                == event.event_id
            )
        )


        existing_prediction = (
            existing_result.scalars().first()
        )


        if existing_prediction:

            print(
                "Prediction already exists for event:",
                event.event_id
            )

            return existing_prediction


        # ----------------------------------------------------
        # Prepare prediction input data
        # ----------------------------------------------------

        prediction_input = dict(
            event.input_data
            or {}
        )


        prediction_input[
            "ml_features"
        ] = result[
            "features"
        ]


        prediction_input[
            "model_confidence"
        ] = result[
            "model_confidence"
        ]


        prediction_input[
            "class_probabilities"
        ] = result[
            "class_probabilities"
        ]


        prediction_input[
            "model_type"
        ] = "XGBClassifier"


        # ----------------------------------------------------
        # Create PredictionModel
        # ----------------------------------------------------

        prediction = PredictionModel(

            disaster_type=(
                "forest_fire"
            ),

            region=(
                event.region
            ),

            predicted_time=(
                event.event_time
            ),

            input_data=(
                prediction_input
            ),

            risk_score=(
                result[
                    "risk_score"
                ]
            ),

            severity_tier=(
                result[
                    "severity_tier"
                ]
            ),

            matched_event_id=(
                event.event_id
            ),

            is_simulated=(
                event.source != "real"
            )

        )


        session.add(
            prediction
        )


        await session.commit()


        await session.refresh(
            prediction
        )


        print(
            "\n------------------------------------------"
        )

        print(
            "FOREST FIRE PREDICTION CREATED"
        )

        print(
            "------------------------------------------"
        )

        print(
            "Event ID:",
            event.event_id
        )

        print(
            "Severity:",
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
            "------------------------------------------"
        )


        return prediction


# ============================================================
# 8. PREDICT LATEST UNPROCESSED EVENTS
# ============================================================

async def process_pending_predictions():

    async with async_session() as session:

        # ----------------------------------------------------
        # Find forest fire events that don't have a prediction
        # ----------------------------------------------------

        result = await session.execute(

            select(
                EventModel
            )
            .outerjoin(

                PredictionModel,

                PredictionModel.matched_event_id
                == EventModel.event_id

            )
            .where(

                EventModel.disaster_type
                == "forest_fire"

            )
            .where(

                PredictionModel.prediction_id
                == None

            )
            .order_by(

                EventModel.event_time.desc()

            )
            .limit(100)

        )


        events = (
            result.scalars().all()
        )


    if not events:

        print(
            "\nNo pending forest fire events."
        )

        return []


    print(
        f"\nPending forest fire events: "
        f"{len(events)}"
    )


    predictions = []


    for event in events:

        try:

            prediction = await save_prediction(
                event
            )

            predictions.append(
                prediction
            )

        except Exception as e:

            print(
                "Prediction error for event",
                event.event_id,
                ":",
                e
            )


    return predictions


# ============================================================
# 9. PREDICT NOW
# ============================================================

async def predict_now():

    print(
        "\n=========================================="
    )

    print(
        "FOREST FIRE PREDICT NOW"
    )

    print(
        "=========================================="
    )


    predictions = (
        await process_pending_predictions()
    )


    print(
        f"\nPredictions created: "
        f"{len(predictions)}"
    )


    return predictions


# ============================================================
# 10. AUTOMATIC PREDICTION LOOP
# ============================================================

async def start_prediction_polling():

    print(
        "\n=========================================="
    )

    print(
        "FOREST FIRE ML PREDICTION LOOP STARTED"
    )

    print(
        "=========================================="
    )


    # --------------------------------------------------------
    # Run once immediately
    # --------------------------------------------------------

    try:

        await process_pending_predictions()

    except Exception as e:

        print(
            "Initial prediction error:",
            e
        )


    # --------------------------------------------------------
    # Continue periodically
    # --------------------------------------------------------

    while True:

        await asyncio.sleep(
            POLL_INTERVAL_SECONDS
        )


        try:

            await process_pending_predictions()

        except Exception as e:

            print(
                "Forest Fire Prediction Poll Error:",
                e
            )