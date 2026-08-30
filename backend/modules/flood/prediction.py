import os
import json
import zipfile
import tempfile
import asyncio

import joblib
import numpy as np
from tensorflow.keras.models import load_model


# ============================================================
# FLOOD PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

FLOOD_ARTIFACTS_DIR = os.path.join(
    BASE_DIR,
    "ml_artifacts",
    "flood_artifacts"
)

MODEL_PATH = os.path.join(
    FLOOD_ARTIFACTS_DIR,
    "flood_corrected_lstm.keras"
)

SCALER_PATH = os.path.join(
    FLOOD_ARTIFACTS_DIR,
    "flood_scaler.pkl"
)

FEATURE_REFERENCE_PATH = os.path.join(
    FLOOD_ARTIFACTS_DIR,
    "flood_feature_reference.json"
)


# ============================================================
# CHECK FLOOD ARTIFACTS
# ============================================================

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Flood model not found: {MODEL_PATH}"
    )

if not os.path.exists(SCALER_PATH):
    raise FileNotFoundError(
        f"Flood scaler not found: {SCALER_PATH}"
    )

if not os.path.exists(FEATURE_REFERENCE_PATH):
    raise FileNotFoundError(
        f"Flood feature reference not found: "
        f"{FEATURE_REFERENCE_PATH}"
    )


# ============================================================
# KERAS COMPATIBILITY LOADER
# ============================================================

def _load_flood_model_compatible(model_path):

    def clean_config(obj):

        if isinstance(obj, dict):

            if obj.get("class_name") == "GlorotUniform":

                old_config = obj.get(
                    "config",
                    {}
                )

                obj["config"] = {
                    "seed": old_config.get(
                        "seed",
                        None
                    )
                }

            for key in list(obj.keys()):

                obj[key] = clean_config(
                    obj[key]
                )

            return obj

        if isinstance(obj, list):

            return [
                clean_config(item)
                for item in obj
            ]

        return obj

    fixed_model_path = os.path.join(
        tempfile.gettempdir(),
        "flood_corrected_lstm_fixed.keras"
    )

    with zipfile.ZipFile(
        model_path,
        "r"
    ) as zin:

        with zipfile.ZipFile(
            fixed_model_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zout:

            for item in zin.infolist():

                data = zin.read(
                    item.filename
                )

                if item.filename == "config.json":

                    config = json.loads(
                        data.decode("utf-8")
                    )

                    config = clean_config(
                        config
                    )

                    data = json.dumps(
                        config
                    ).encode("utf-8")

                zout.writestr(
                    item,
                    data
                )

    return load_model(
        fixed_model_path,
        compile=False
    )


# ============================================================
# LOAD FLOOD MODEL
# ============================================================

model = _load_flood_model_compatible(
    MODEL_PATH
)

print("Flood LSTM model loaded.")

print(
    "Flood model input shape:",
    model.input_shape
)


# ============================================================
# LOAD FLOOD SCALER
# ============================================================

scaler = joblib.load(
    SCALER_PATH
)

print("Flood scaler loaded.")


# ============================================================
# LOAD FEATURE REFERENCE
# ============================================================

with open(
    FEATURE_REFERENCE_PATH,
    "r"
) as f:

    feature_reference = json.load(f)


FEATURE_COLUMNS = feature_reference[
    "features"
]

print("Flood feature reference loaded.")

print(
    "Features:",
    FEATURE_COLUMNS
)

print(
    "Number of Flood features:",
    len(FEATURE_COLUMNS)
)


# ============================================================
# SAFE FLOAT CONVERSION
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
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(features):

    values = []

    for column in FEATURE_COLUMNS:

        value = features.get(
            column,
            0.0
        )

        values.append(
            _to_float(value)
        )

    return np.array(
        values,
        dtype=np.float32
    )


# ============================================================
# CREATE MODEL INPUT
# ============================================================

def _create_model_input(scaled_features):

    expected_shape = model.input_shape

    # --------------------------------------------------------
    # Model expects (batch, 20, 5)
    # --------------------------------------------------------

    if (
        len(expected_shape) == 3
        and expected_shape[1] == 20
        and expected_shape[2] == 5
    ):

        model_input = np.repeat(
            scaled_features.reshape(
                1,
                20,
                1
            ),
            5,
            axis=2
        )

        return model_input.astype(
            np.float32
        )

    # --------------------------------------------------------
    # Model expects (batch, 20, 1)
    # --------------------------------------------------------

    if (
        len(expected_shape) == 3
        and expected_shape[1] == 20
        and expected_shape[2] == 1
    ):

        return scaled_features.reshape(
            1,
            20,
            1
        ).astype(
            np.float32
        )

    raise ValueError(
        f"Unsupported Flood model input shape: "
        f"{expected_shape}"
    )


# ============================================================
# FLOOD PREDICTION
# ============================================================

def predict_flood(features):

    # --------------------------------------------------------
    # Prepare 20 flood features
    # --------------------------------------------------------

    feature_array = prepare_features(
        features
    )

    expected_features = len(
        FEATURE_COLUMNS
    )

    if len(feature_array) != expected_features:

        raise ValueError(
            f"Expected {expected_features} "
            f"features, got {len(feature_array)}"
        )

    # --------------------------------------------------------
    # Scale features
    # --------------------------------------------------------

    scaled_features = scaler.transform(
        feature_array.reshape(
            1,
            -1
        )
    )

    scaled_features = np.asarray(
        scaled_features,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Prepare LSTM input
    # --------------------------------------------------------

    model_input = _create_model_input(
        scaled_features[0]
    )

    print(
        "Flood model input shape:",
        model_input.shape
    )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    prediction = model.predict(
        model_input,
        verbose=0
    )

    probability = float(
        np.asarray(
            prediction
        ).reshape(-1)[0]
    )

    # --------------------------------------------------------
    # Keep probability between 0 and 1
    # --------------------------------------------------------

    probability = max(
        0.0,
        min(
            probability,
            1.0
        )
    )

    probability_percent = (
        probability * 100
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    if probability >= 0.90:

        severity = "critical"

    elif probability >= 0.70:

        severity = "high"

    elif probability >= 0.40:

        severity = "medium"

    else:

        severity = "low"

    return {

        "flood_probability": round(
            probability,
            4
        ),

        "flood_probability_percent": round(
            probability_percent,
            2
        ),

        "severity": severity
    }


# ============================================================
# PREDICT EVENT
# Used by modules/flood/routes.py
# ============================================================

def predict_event(event):

    if event is None:

        raise ValueError(
            "Flood event cannot be None."
        )

    input_data = event.input_data or {}

    # --------------------------------------------------------
    # Run flood prediction
    # --------------------------------------------------------

    prediction = predict_flood(
        input_data
    )

    probability = prediction[
        "flood_probability"
    ]

    probability_percent = prediction[
        "flood_probability_percent"
    ]

    severity = prediction[
        "severity"
    ]

    # --------------------------------------------------------
    # Risk score
    # --------------------------------------------------------

    risk_score = round(
        probability_percent,
        2
    )

    # --------------------------------------------------------
    # Return result expected by routes.py
    # --------------------------------------------------------

    return {

        "flood_probability": round(
            probability,
            4
        ),

        "risk_score": risk_score,

        "severity_tier": severity,

        "features": {

            column: _to_float(
                input_data.get(
                    column,
                    0.0
                )
            )

            for column in FEATURE_COLUMNS

        }
    }


# ============================================================
# FLOOD PREDICTION POLLING
# Used by main.py
# ============================================================

async def start_prediction_polling():

    print(
        "Flood prediction polling started."
    )

    while True:

        try:

            # Prediction is currently triggered
            # through the prediction endpoint.

            await asyncio.sleep(
                3600
            )

        except asyncio.CancelledError:

            print(
                "Flood prediction polling stopped."
            )

            raise

        except Exception as e:

            print(
                "Flood prediction polling error:",
                e
            )

            await asyncio.sleep(
                60
            )


# ============================================================
# READY
# ============================================================

print(
    "Flood prediction module ready."
)