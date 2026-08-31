
# ============================================================
# CYCLONE ML PREDICTION
# CNN-LSTM INFERENCE
# ============================================================

import os
import json
import asyncio
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
import httpx

from db import async_session
from models import PredictionModel

from modules.cyclone.config import (
    WEATHER_API_URL,
    WEATHER_API_KEY,
    POLL_INTERVAL_SECONDS,
    CYCLONE_MONITOR_LOCATIONS,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

ARTIFACT_DIR = os.path.join(
    PROJECT_ROOT,
    "ml_artifacts",
    "cyclone_artifacts"
)

MODEL_PATH = os.path.join(
    ARTIFACT_DIR,
    "cyclone_cnn_lstm.keras"
)

SCALER_PATH = os.path.join(
    ARTIFACT_DIR,
    "cyclone_scaler.pkl"
)

REFERENCE_PATH = os.path.join(
    ARTIFACT_DIR,
    "cyclone_feature_reference.json"
)


# ============================================================
# KERAS COMPATIBILITY FIX
#
# The saved model contains:
#
#   GlorotUniform:
#       input_axes
#       output_axes
#
# Some Keras versions cannot deserialize these old fields.
#
# This compatibility initializer removes those unsupported
# fields before creating GlorotUniform.
# ============================================================

try:

    OriginalGlorotUniform = tf.keras.initializers.GlorotUniform


    @tf.keras.utils.register_keras_serializable(
        package="Compatibility"
    )
    class CompatibleGlorotUniform(
        OriginalGlorotUniform
    ):

        @classmethod
        def from_config(
            cls,
            config
        ):

            config = dict(config)

            # Remove fields unsupported by the
            # currently installed Keras version.

            config.pop(
                "input_axes",
                None
            )

            config.pop(
                "output_axes",
                None
            )

            return cls(
                **config
            )


except Exception as e:

    print(
        "[Cyclone ML] "
        "Keras compatibility initializer setup failed:",
        e
    )


# ============================================================
# START
# ============================================================

print(
    "========================================"
)

print(
    "CYCLONE ML PREDICTION"
)

print(
    "========================================"
)


# ============================================================
# LOAD FEATURE REFERENCE
# ============================================================

print(
    "Loading feature reference..."
)

if not os.path.exists(
    REFERENCE_PATH
):

    raise FileNotFoundError(
        f"Feature reference not found:\n"
        f"{REFERENCE_PATH}"
    )


with open(
    REFERENCE_PATH,
    "r",
    encoding="utf-8"
) as file:

    FEATURE_REFERENCE = json.load(
        file
    )


FEATURES = FEATURE_REFERENCE[
    "features"
]

SEQUENCE_LENGTH = FEATURE_REFERENCE[
    "sequence_length"
]

PREDICTION_THRESHOLD = FEATURE_REFERENCE.get(
    "prediction_threshold",
    0.5
)


print(
    f"Sequence length: {SEQUENCE_LENGTH}"
)

print(
    f"Number of features: {len(FEATURES)}"
)

print(
    f"Prediction threshold: "
    f"{PREDICTION_THRESHOLD}"
)


# ============================================================
# VERIFY FEATURE COUNT
# ============================================================

EXPECTED_FEATURE_COUNT = 13


if len(FEATURES) != EXPECTED_FEATURE_COUNT:

    raise ValueError(
        "Unexpected Cyclone feature count. "
        f"Expected {EXPECTED_FEATURE_COUNT}, "
        f"got {len(FEATURES)}"
    )


# ============================================================
# LOAD SCALER
# ============================================================

print(
    "\nLoading Cyclone scaler..."
)

if not os.path.exists(
    SCALER_PATH
):

    raise FileNotFoundError(
        f"Cyclone scaler not found:\n"
        f"{SCALER_PATH}"
    )


scaler = joblib.load(
    SCALER_PATH
)


print(
    "Cyclone scaler loaded successfully."
)


# ============================================================
# VERIFY SCALER FEATURE COUNT
# ============================================================

if hasattr(
    scaler,
    "n_features_in_"
):

    if scaler.n_features_in_ != len(FEATURES):

        raise ValueError(
            "Scaler feature count does not match "
            "feature reference.\n"
            f"Scaler: {scaler.n_features_in_}\n"
            f"Features: {len(FEATURES)}"
        )


# ============================================================
# LOAD CNN-LSTM MODEL
# ============================================================

print(
    "\nLoading Cyclone CNN-LSTM model..."
)

if not os.path.exists(
    MODEL_PATH
):

    raise FileNotFoundError(
        f"Cyclone CNN-LSTM model not found:\n"
        f"{MODEL_PATH}"
    )


try:

    model = tf.keras.models.load_model(
        MODEL_PATH,
        compile=False
    )

except Exception as first_error:

    print(
        "\nStandard Keras model loading failed."
    )

    print(
        "Attempting compatibility loading..."
    )

    try:

        # Register compatibility class under the name
        # used by the saved model.

        tf.keras.utils.get_custom_objects()[
            "GlorotUniform"
        ] = CompatibleGlorotUniform

        tf.keras.utils.get_custom_objects()[
            "keras.initializers.GlorotUniform"
        ] = CompatibleGlorotUniform

        model = tf.keras.models.load_model(
            MODEL_PATH,
            compile=False,
            custom_objects={
                "GlorotUniform":
                    CompatibleGlorotUniform,
                "keras.initializers.GlorotUniform":
                    CompatibleGlorotUniform,
            }
        )

    except Exception as second_error:

        print(
            "\n========================================"
        )

        print(
            "CYCLONE MODEL LOADING FAILED"
        )

        print(
            "========================================"
        )

        print(
            "\nFirst loading error:"
        )

        print(
            first_error
        )

        print(
            "\nCompatibility loading error:"
        )

        print(
            second_error
        )

        print(
            "\nThe cyclone model was saved using a "
            "different Keras version."
        )

        raise


print(
    "Cyclone CNN-LSTM loaded successfully."
)


# ============================================================
# PRINT MODEL INPUT
# ============================================================

print(
    "\nModel input shape:"
)

print(
    model.input_shape
)


# ============================================================
# VERIFY MODEL INPUT
# ============================================================

expected_shape = (
    None,
    SEQUENCE_LENGTH,
    len(FEATURES)
)


if model.input_shape != expected_shape:

    print(
        "\nWARNING:"
    )

    print(
        "Expected model input shape:",
        expected_shape
    )

    print(
        "Actual model input shape:",
        model.input_shape
    )


# ============================================================
# IN-MEMORY OBSERVATION HISTORY
#
# CNN-LSTM requires 12 observations.
#
# Each configured location has its own history.
# ============================================================

location_history = {}


# ============================================================
# FETCH WEATHER
# ============================================================

async def fetch_weather(
    lat,
    lon
):

    params = {

        "lat": lat,

        "lon": lon,

        "appid": WEATHER_API_KEY,

        "units": "metric",

    }


    async with httpx.AsyncClient() as client:

        response = await client.get(

            WEATHER_API_URL,

            params=params,

            timeout=10,

        )


        response.raise_for_status()


        return response.json()


# ============================================================
# CREATE FEATURE ROW
# ============================================================

def create_feature_row(
    weather,
    location,
    previous_wind=None
):

    now = datetime.now(
        timezone.utc
    )


    # --------------------------------------------------------
    # Current wind
    #
    # OpenWeather gives wind speed in m/s.
    # Convert to km/h.
    # --------------------------------------------------------

    current_wind = (

        float(
            weather["wind"]["speed"]
        )

        * 3.6

    )


    # --------------------------------------------------------
    # Pressure
    # --------------------------------------------------------

    pressure = float(
        weather["main"]["pressure"]
    )


    # --------------------------------------------------------
    # Wind direction
    # --------------------------------------------------------

    storm_dir = float(

        weather["wind"].get(
            "deg",
            0
        )

    )


    # --------------------------------------------------------
    # Previous wind
    # --------------------------------------------------------

    if previous_wind is None:

        previous_wind = current_wind


    previous_wind = float(
        previous_wind
    )


    # --------------------------------------------------------
    # Wind change
    # --------------------------------------------------------

    wind_change = (

        current_wind
        -
        previous_wind

    )


    # --------------------------------------------------------
    # Storm speed
    # --------------------------------------------------------

    storm_speed = float(

        location.get(
            "storm_speed",
            current_wind
        )

    )


    # --------------------------------------------------------
    # Distance to land
    # --------------------------------------------------------

    dist2land = float(

        location.get(
            "dist2land",
            0
        )

    )


    # --------------------------------------------------------
    # Build feature dictionary
    # --------------------------------------------------------

    row = {

        "LAT": float(
            location["lat"]
        ),

        "LON": float(
            location["lon"]
        ),

        "WMO_WIND": current_wind,

        "WMO_PRES": pressure,

        "STORM_SPEED": storm_speed,

        "STORM_DIR": storm_dir,

        "DIST2LAND": dist2land,

        "previous_wind": previous_wind,

        "wind_change": wind_change,

        "year": now.year,

        "month": now.month,

        "day": now.day,

        "hour": now.hour,

    }


    return row


# ============================================================
# PREPARE CNN-LSTM INPUT
# ============================================================

def prepare_sequence(
    history
):

    if len(history) < SEQUENCE_LENGTH:

        return None


    recent = history[
        -SEQUENCE_LENGTH:
    ]


    df = pd.DataFrame(
        recent
    )


    # --------------------------------------------------------
    # EXACT FEATURE ORDER FROM TRAINING
    # --------------------------------------------------------

    df = df[
        FEATURES
    ]


    values = df.values.astype(
        np.float32
    )


    # --------------------------------------------------------
    # APPLY TRAINING SCALER
    # --------------------------------------------------------

    scaled = scaler.transform(
        values
    )


    # --------------------------------------------------------
    # SHAPE:
    #
    # (1, 12, 13)
    # --------------------------------------------------------

    X = scaled.reshape(

        1,

        SEQUENCE_LENGTH,

        len(FEATURES)

    )


    return X


# ============================================================
# CONVERT PROBABILITY TO SEVERITY
# ============================================================

def get_severity(
    probability
):

    if probability >= 0.80:

        return "critical"

    elif probability >= 0.60:

        return "high"

    elif probability >= 0.40:

        return "medium"

    else:

        return "low"


# ============================================================
# CNN-LSTM PREDICTION
# ============================================================

def predict_cyclone(
    history
):

    X = prepare_sequence(
        history
    )


    if X is None:

        return None


    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    raw_prediction = model.predict(
        X,
        verbose=0
    )


    probability = float(
        np.asarray(
            raw_prediction
        ).reshape(-1)[0]
    )


    probability = max(
        0.0,
        min(
            1.0,
            probability
        )
    )


    severity = get_severity(
        probability
    )


    intensifies = (

        probability
        >=
        PREDICTION_THRESHOLD

    )


    return {

        "prediction_probability":
            probability,

        "risk_score":
            probability,

        "severity_tier":
            severity,

        "predicted_intensification":
            intensifies,

    }


# ============================================================
# SAVE PREDICTION TO DATABASE
# ============================================================

async def save_prediction(
    location,
    feature_row,
    prediction
):

    if prediction is None:

        return None


    row = PredictionModel(

        disaster_type="cyclone",

        region=location[
            "region"
        ],

        predicted_time=datetime.now(
            timezone.utc
        ),

        input_data={

            "features":
                feature_row,

            "prediction_probability":
                prediction[
                    "prediction_probability"
                ],

            "predicted_intensification":
                prediction[
                    "predicted_intensification"
                ],

        },

        risk_score=prediction[
            "risk_score"
        ],

        severity_tier=prediction[
            "severity_tier"
        ],

        matched_event_id=None,

        is_simulated=False,

    )


    async with async_session() as session:

        session.add(
            row
        )

        await session.commit()

        await session.refresh(
            row
        )


    return row


# ============================================================
# PROCESS ONE LOCATION
# ============================================================

async def process_location(
    location
):

    region = location[
        "region"
    ]


    try:

        weather = await fetch_weather(

            location["lat"],

            location["lon"]

        )


        # ----------------------------------------------------
        # UNIQUE HISTORY KEY
        # ----------------------------------------------------

        history_key = (

            f"{location['lat']}_"
            f"{location['lon']}"

        )


        if history_key not in location_history:

            location_history[
                history_key
            ] = []


        history = location_history[
            history_key
        ]


        # ----------------------------------------------------
        # PREVIOUS WIND
        # ----------------------------------------------------

        previous_wind = None


        if history:

            previous_wind = history[
                -1
            ]["WMO_WIND"]


        # ----------------------------------------------------
        # CURRENT FEATURE ROW
        # ----------------------------------------------------

        feature_row = create_feature_row(

            weather,

            location,

            previous_wind

        )


        # ----------------------------------------------------
        # ADD OBSERVATION
        # ----------------------------------------------------

        history.append(
            feature_row
        )


        # ----------------------------------------------------
        # KEEP ONLY REQUIRED HISTORY
        # ----------------------------------------------------

        if len(history) > SEQUENCE_LENGTH:

            del history[
                :-SEQUENCE_LENGTH
            ]


        # ----------------------------------------------------
        # WAIT UNTIL 12 OBSERVATIONS EXIST
        # ----------------------------------------------------

        if len(history) < SEQUENCE_LENGTH:

            print(

                f"[Cyclone ML] "
                f"{region}: "
                f"collecting "
                f"{len(history)}/"
                f"{SEQUENCE_LENGTH}"

            )

            return None


        # ----------------------------------------------------
        # MAKE PREDICTION
        # ----------------------------------------------------

        prediction = predict_cyclone(
            history
        )


        if prediction is None:

            return None


        print(
            "\n----------------------------------------"
        )

        print(
            "CYCLONE ML PREDICTION"
        )

        print(
            "----------------------------------------"
        )

        print(
            f"Region: {region}"
        )

        print(

            "Probability: "
            f"{prediction['prediction_probability']:.4f}"

        )

        print(

            "Risk score: "
            f"{prediction['risk_score']:.4f}"

        )

        print(

            f"Severity: "
            f"{prediction['severity_tier']}"

        )

        print(

            "Predicted intensification: "
            f"{prediction['predicted_intensification']}"

        )


        # ----------------------------------------------------
        # SAVE PREDICTION
        # ----------------------------------------------------

        await save_prediction(

            location,

            feature_row,

            prediction

        )


        return prediction


    except Exception as e:

        print(

            f"[Cyclone ML Error] "
            f"{region}: {e}"

        )

        return None


# ============================================================
# PREDICTION POLLING LOOP
# ============================================================

async def start_prediction_polling():

    print(
        "========================================"
    )

    print(
        "Cyclone ML prediction polling started"
    )

    print(
        "========================================"
    )


    while True:

        try:

            for location in (
                CYCLONE_MONITOR_LOCATIONS
            ):

                await process_location(
                    location
                )


        except Exception as e:

            print(
                "[Cyclone ML Poll Error]:",
                e
            )


        await asyncio.sleep(
            POLL_INTERVAL_SECONDS
        )

