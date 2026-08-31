# ============================================================
# CYCLONE ARTIFACT CREATION
#
# Creates backend deployment artifacts:
#
# 1. cyclone_scaler.pkl
# 2. cyclone_feature_reference.json
# 3. cyclone_cnn_lstm.keras
#
# The scaler is fitted ONLY on the training cyclone data.
# ============================================================

import os
import json
import shutil

import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import StandardScaler


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        ".."
    )
)


# ------------------------------------------------------------
# Processed dataset
# ------------------------------------------------------------

PROCESSED_FILE = os.path.join(
    PROJECT_ROOT,
    "ml_training",
    "cyclone",
    "data",
    "processed",
    "cyclone_processed.csv"
)


# ------------------------------------------------------------
# Training model
# ------------------------------------------------------------

MODEL_FILE = os.path.join(
    PROJECT_ROOT,
    "ml_training",
    "cyclone",
    "models",
    "cyclone_cnn_lstm.keras"
)


# ------------------------------------------------------------
# Backend artifact directory
# ------------------------------------------------------------

ARTIFACT_DIR = os.path.join(
    PROJECT_ROOT,
    "backend",
    "ml_artifacts",
    "cyclone_artifacts"
)


os.makedirs(
    ARTIFACT_DIR,
    exist_ok=True
)


# ------------------------------------------------------------
# Output artifacts
# ------------------------------------------------------------

SCALER_FILE = os.path.join(
    ARTIFACT_DIR,
    "cyclone_scaler.pkl"
)

REFERENCE_FILE = os.path.join(
    ARTIFACT_DIR,
    "cyclone_feature_reference.json"
)

DEPLOYED_MODEL_FILE = os.path.join(
    ARTIFACT_DIR,
    "cyclone_cnn_lstm.keras"
)


# ============================================================
# 2. FEATURES
# ============================================================

FEATURE_COLUMNS = [

    "LAT",
    "LON",
    "WMO_WIND",
    "WMO_PRES",
    "STORM_SPEED",
    "STORM_DIR",
    "DIST2LAND",
    "previous_wind",
    "wind_change",
    "year",
    "month",
    "day",
    "hour",

]


# ============================================================
# 3. RANDOM SEED
#
# MUST MATCH TRAINING SCRIPT
# ============================================================

SEED = 42


# ============================================================
# 4. SEQUENCE LENGTH
# ============================================================

SEQUENCE_LENGTH = 12


# ============================================================
# 5. PRINT HEADER
# ============================================================

print("=" * 40)

print(
    "CYCLONE ARTIFACT CREATION"
)

print("=" * 40)


# ============================================================
# 6. CHECK PROCESSED DATASET
# ============================================================

if not os.path.exists(
    PROCESSED_FILE
):

    raise FileNotFoundError(
        "\nProcessed cyclone dataset not found:\n"
        f"{PROCESSED_FILE}\n\n"
        "Run preprocessing first:\n"
        "python ml_training/cyclone/src/preprocess.py"
    )


# ============================================================
# 7. LOAD DATASET
# ============================================================

print(
    "\nLoading processed cyclone dataset..."
)

data = pd.read_csv(
    PROCESSED_FILE
)

print(
    f"Rows loaded: {len(data)}"
)

print(
    f"Cyclones: {data['SID'].nunique()}"
)


# ============================================================
# 8. VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [

    "SID",

] + FEATURE_COLUMNS + [

    "intensifies"

]


missing = [

    column
    for column in required_columns
    if column not in data.columns

]


if missing:

    raise ValueError(
        "\nMissing columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# 9. CLEAN DATA
# ============================================================

data = data.copy()


data = data.dropna(
    subset=FEATURE_COLUMNS + ["intensifies"]
)


data = data.sort_values(
    [
        "SID",
        "ISO_TIME"
    ]
).reset_index(
    drop=True
)


print(
    f"Rows after cleaning: {len(data)}"
)

print(
    "Cyclones after cleaning: "
    f"{data['SID'].nunique()}"
)


# ============================================================
# 10. REPRODUCE CYCLONE-LEVEL SPLIT
#
# IMPORTANT:
# We split entire cyclones, not individual rows.
#
# This prevents the same cyclone from appearing in
# both training and validation/test sets.
# ============================================================

cyclones = (
    data["SID"]
    .unique()
    .to_numpy()
    .copy()
)


rng = np.random.default_rng(
    SEED
)


rng.shuffle(
    cyclones
)


n_cyclones = len(
    cyclones
)


train_end = int(
    n_cyclones * 0.70
)

validation_end = int(
    n_cyclones * 0.85
)


train_cyclones = cyclones[
    :train_end
]


validation_cyclones = cyclones[
    train_end:validation_end
]


test_cyclones = cyclones[
    validation_end:
]


print(
    "\nDataset split reproduced:"
)

print(
    f"Train cyclones: "
    f"{len(train_cyclones)}"
)

print(
    f"Validation cyclones: "
    f"{len(validation_cyclones)}"
)

print(
    f"Test cyclones: "
    f"{len(test_cyclones)}"
)


# ============================================================
# 11. CREATE TRAINING DATA ONLY
# ============================================================

train_data = data[
    data["SID"].isin(
        train_cyclones
    )
].copy()


print(
    "\nTraining rows used for scaler:"
    f" {len(train_data)}"
)


# ============================================================
# 12. CREATE STANDARD SCALER
#
# VERY IMPORTANT:
#
# Fit scaler ONLY on training data.
#
# Do NOT fit on validation or test data.
# ============================================================

print(
    "\nCreating StandardScaler..."
)


scaler = StandardScaler()


X_train = train_data[
    FEATURE_COLUMNS
].astype(
    np.float32
)


scaler.fit(
    X_train
)


# ============================================================
# 13. SAVE SCALER
# ============================================================

joblib.dump(
    scaler,
    SCALER_FILE
)


print(
    "\nScaler saved:"
)

print(
    SCALER_FILE
)


# ============================================================
# 14. CREATE FEATURE REFERENCE
# ============================================================

feature_reference = {

    "disaster_type": "cyclone",

    "model_type": "CNN-LSTM",

    "target": "intensifies",

    "target_description":
        "1 = next observation has higher wind, "
        "0 = next observation has same or lower wind",

    "sequence_length":
        SEQUENCE_LENGTH,

    "features":
        FEATURE_COLUMNS,

    "number_of_features":
        len(FEATURE_COLUMNS),

    "scaler":
        "StandardScaler",

    "scaler_fitted_on":
        "training_cyclones_only",

    "train_split":
        0.70,

    "validation_split":
        0.15,

    "test_split":
        0.15,

    "seed":
        SEED,

}


with open(
    REFERENCE_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        feature_reference,
        file,
        indent=4
    )


print(
    "\nFeature reference saved:"
)

print(
    REFERENCE_FILE
)


# ============================================================
# 15. COPY CNN-LSTM MODEL
# ============================================================

if not os.path.exists(
    MODEL_FILE
):

    raise FileNotFoundError(
        "\nCNN-LSTM model not found:\n"
        f"{MODEL_FILE}\n\n"
        "Make sure the trained model exists in:\n"
        "ml_training/cyclone/models/"
    )


shutil.copy2(
    MODEL_FILE,
    DEPLOYED_MODEL_FILE
)


print(
    "\nCNN-LSTM model copied:"
)

print(
    DEPLOYED_MODEL_FILE
)


# ============================================================
# 16. VERIFY ARTIFACTS
# ============================================================

print(
    "\n" + "=" * 40
)

print(
    "CYCLONE ARTIFACTS"
)

print(
    "=" * 40
)


artifacts = [

    DEPLOYED_MODEL_FILE,

    REFERENCE_FILE,

    SCALER_FILE,

]


for artifact in artifacts:

    if os.path.exists(
        artifact
    ):

        size = os.path.getsize(
            artifact
        )

        print(
            f"{artifact}"
        )

        print(
            f"  Size: {size:,} bytes"
        )

    else:

        print(
            f"MISSING: {artifact}"
        )


# ============================================================
# 17. FINISH
# ============================================================

print(
    "\n" + "=" * 40
)

print(
    "ARTIFACT CREATION COMPLETE"
)

print(
    "=" * 40
)