import os
import random
import json
import joblib

import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)

from imblearn.over_sampling import SMOTE

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Input,
    Conv1D,
    MaxPooling1D,
    LSTM,
    Dense,
    Dropout,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping


# ============================================================
# Reproducibility
# ============================================================

SEED = 42

np.random.seed(SEED)
random.seed(SEED)
tf.random.set_seed(SEED)


# ============================================================
# PROJECT PATHS
# ============================================================

# Current file:
# ml_training/cyclone/src/train_cnn_lstm.py
#
# Project root:
# ../../..
#
# Therefore we build all paths from this file location.

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        "..",
        "..",
        ".."
    )
)


# ============================================================
# Training paths
# ============================================================

DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "ml_training",
    "cyclone",
    "data",
    "processed",
    "cyclone_processed.csv"
)

MODEL_DIR = os.path.join(
    PROJECT_ROOT,
    "ml_training",
    "cyclone",
    "models"
)

RESULT_DIR = os.path.join(
    PROJECT_ROOT,
    "ml_training",
    "cyclone",
    "results"
)

PREDICTION_DIR = os.path.join(
    PROJECT_ROOT,
    "ml_training",
    "cyclone",
    "predictions"
)


# ============================================================
# Backend deployment artifacts
# ============================================================

ARTIFACT_DIR = os.path.join(
    PROJECT_ROOT,
    "backend",
    "ml_artifacts",
    "cyclone_artifacts"
)


# ============================================================
# Create directories
# ============================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

os.makedirs(
    RESULT_DIR,
    exist_ok=True
)

os.makedirs(
    PREDICTION_DIR,
    exist_ok=True
)

os.makedirs(
    ARTIFACT_DIR,
    exist_ok=True
)


print("========================================")
print("CYCLONE CNN-LSTM TRAINING")
print("========================================")

print("\nProject root:")
print(PROJECT_ROOT)

print("\nDeployment artifact directory:")
print(ARTIFACT_DIR)


# ============================================================
# Load dataset
# ============================================================

print("\nLoading processed cyclone dataset...")

data = pd.read_csv(
    DATA_PATH
)

print(
    f"Rows loaded: {len(data)}"
)

print(
    f"Cyclones: {data['SID'].nunique()}"
)


# ============================================================
# Features and target
# ============================================================

FEATURES = [
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

TARGET = "intensifies"


# ============================================================
# Make sure numeric columns are numeric
# ============================================================

for col in FEATURES:

    data[col] = pd.to_numeric(
        data[col],
        errors="coerce"
    )


data[TARGET] = pd.to_numeric(
    data[TARGET],
    errors="coerce"
)


# ============================================================
# Remove missing values
# ============================================================

data = data.dropna(
    subset=FEATURES + [TARGET]
).copy()


# ============================================================
# Sort data
# ============================================================

data = data.sort_values(
    ["SID", "ISO_TIME"]
).reset_index(
    drop=True
)


print(
    f"Rows after final cleaning: {len(data)}"
)

print(
    f"Cyclones after final cleaning: "
    f"{data['SID'].nunique()}"
)


# ============================================================
# Split by cyclone
#
# IMPORTANT:
# One cyclone must belong to only one split.
# ============================================================

cyclones = data["SID"].unique()


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

val_end = int(
    n_cyclones * 0.85
)


train_ids = cyclones[
    :train_end
]

val_ids = cyclones[
    train_end:val_end
]

test_ids = cyclones[
    val_end:
]


train_df = data[
    data["SID"].isin(train_ids)
].copy()


val_df = data[
    data["SID"].isin(val_ids)
].copy()


test_df = data[
    data["SID"].isin(test_ids)
].copy()


print("\n========================================")
print("DATASET SPLIT")
print("========================================")

print(
    f"Train cyclones: {len(train_ids)}"
)

print(
    f"Validation cyclones: {len(val_ids)}"
)

print(
    f"Test cyclones: {len(test_ids)}"
)

print(
    f"Train rows: {len(train_df)}"
)

print(
    f"Validation rows: {len(val_df)}"
)

print(
    f"Test rows: {len(test_df)}"
)


# ============================================================
# Scale features
#
# IMPORTANT:
# Fit scaler ONLY on training data.
# ============================================================

print("\nScaling features...")

scaler = StandardScaler()


train_df[FEATURES] = scaler.fit_transform(
    train_df[FEATURES]
)


val_df[FEATURES] = scaler.transform(
    val_df[FEATURES]
)


test_df[FEATURES] = scaler.transform(
    test_df[FEATURES]
)


# ============================================================
# Create sequences
# ============================================================

SEQUENCE_LENGTH = 12


def make_sequences(df):

    X = []
    y = []

    for sid, group in df.groupby(
        "SID"
    ):

        group = group.sort_values(
            "ISO_TIME"
        )

        feature_values = group[
            FEATURES
        ].values

        target_values = group[
            TARGET
        ].values

        if len(group) <= SEQUENCE_LENGTH:
            continue

        for i in range(
            len(group) - SEQUENCE_LENGTH
        ):

            X.append(
                feature_values[
                    i:i + SEQUENCE_LENGTH
                ]
            )

            y.append(
                target_values[
                    i + SEQUENCE_LENGTH
                ]
            )

    return (
        np.array(
            X,
            dtype=np.float32
        ),
        np.array(
            y,
            dtype=np.int32
        )
    )


# ============================================================
# Generate sequences
# ============================================================

X_train, y_train = make_sequences(
    train_df
)

X_val, y_val = make_sequences(
    val_df
)

X_test, y_test = make_sequences(
    test_df
)


print("\n========================================")
print("SEQUENCE SHAPES")
print("========================================")

print(
    "X_train:",
    X_train.shape
)

print(
    "y_train:",
    y_train.shape
)

print(
    "X_val:",
    X_val.shape
)

print(
    "y_val:",
    y_val.shape
)

print(
    "X_test:",
    X_test.shape
)

print(
    "y_test:",
    y_test.shape
)


# ============================================================
# Training class distribution
# ============================================================

print("\n========================================")
print("TRAINING CLASS DISTRIBUTION")
print("========================================")

print(
    pd.Series(
        y_train
    ).value_counts()
)


# ============================================================
# SMOTE
#
# SMOTE works on 2D data.
# Therefore flatten sequences first.
# ============================================================

print("\nApplying SMOTE...")

X_train_flat = X_train.reshape(
    X_train.shape[0],
    -1
)


smote = SMOTE(
    random_state=SEED,
    sampling_strategy=1.0
)


X_train_sm, y_train_sm = (
    smote.fit_resample(
        X_train_flat,
        y_train
    )
)


X_train_sm = X_train_sm.reshape(
    -1,
    SEQUENCE_LENGTH,
    len(FEATURES)
)


print(
    "Training sequences after SMOTE:",
    X_train_sm.shape
)


print(
    "Class distribution after SMOTE:"
)

print(
    pd.Series(
        y_train_sm
    ).value_counts()
)


# ============================================================
# Build CNN-LSTM
# ============================================================

print("\n========================================")
print("BUILDING CNN-LSTM MODEL")
print("========================================")


model = Sequential(
    [

        Input(
            shape=(
                SEQUENCE_LENGTH,
                len(FEATURES)
            )
        ),

        Conv1D(
            filters=32,
            kernel_size=3,
            activation="relu",
            padding="same"
        ),

        MaxPooling1D(
            pool_size=2
        ),

        LSTM(
            32,
            return_sequences=False
        ),

        Dense(
            16,
            activation="relu"
        ),

        Dropout(
            0.3
        ),

        Dense(
            1,
            activation="sigmoid"
        ),

    ]
)


# ============================================================
# Compile
# ============================================================

model.compile(
    optimizer=Adam(
        learning_rate=0.001
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy"
    ]
)


# ============================================================
# Model summary
# ============================================================

model.summary()


# ============================================================
# Early stopping
# ============================================================

early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)


# ============================================================
# Train
# ============================================================

print("\n========================================")
print("TRAINING CNN-LSTM")
print("========================================")


history = model.fit(
    X_train_sm,
    y_train_sm,

    validation_data=(
        X_val,
        y_val
    ),

    epochs=30,

    batch_size=32,

    callbacks=[
        early_stopping
    ],

    verbose=1
)


# ============================================================
# Test predictions
# ============================================================

print("\n========================================")
print("GENERATING TEST PREDICTIONS")
print("========================================")


y_pred_proba = model.predict(
    X_test,
    verbose=0
).ravel()


y_pred = (
    y_pred_proba >= 0.5
).astype(int)


# ============================================================
# Metrics
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)


precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)


recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)


f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)


roc_auc = roc_auc_score(
    y_test,
    y_pred_proba
)


pr_auc = average_precision_score(
    y_test,
    y_pred_proba
)


# ============================================================
# Print results
# ============================================================

print("\n========================================")
print("CNN-LSTM RESULTS")
print("========================================")


print(
    f"Accuracy : {accuracy:.4f}"
)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall   : {recall:.4f}"
)

print(
    f"F1       : {f1:.4f}"
)

print(
    f"ROC-AUC  : {roc_auc:.4f}"
)

print(
    f"PR-AUC   : {pr_auc:.4f}"
)


# ============================================================
# Save training model
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "cyclone_cnn_lstm.keras"
)


model.save(
    model_path
)


print(
    "\nTraining model saved:"
)

print(
    model_path
)


# ============================================================
# Save scaler
# ============================================================

scaler_path = os.path.join(
    ARTIFACT_DIR,
    "cyclone_scaler.pkl"
)


joblib.dump(
    scaler,
    scaler_path
)


print(
    "\nScaler saved:"
)

print(
    scaler_path
)


# ============================================================
# Save deployment model
# ============================================================

artifact_model_path = os.path.join(
    ARTIFACT_DIR,
    "cyclone_cnn_lstm.keras"
)


model.save(
    artifact_model_path
)


print(
    "\nDeployment model saved:"
)

print(
    artifact_model_path
)


# ============================================================
# Save feature reference
# ============================================================

feature_reference = {

    "disaster_type": "cyclone",

    "model": "CNN-LSTM",

    "model_file":
        "cyclone_cnn_lstm.keras",

    "scaler_file":
        "cyclone_scaler.pkl",

    "sequence_length":
        SEQUENCE_LENGTH,

    "features":
        FEATURES,

    "target":
        TARGET,

    "target_description": {
        "0":
            "next observation has same or lower wind",
        "1":
            "next observation has higher wind"
    },

    "threshold":
        0.5

}


feature_reference_path = os.path.join(
    ARTIFACT_DIR,
    "cyclone_feature_reference.json"
)


with open(
    feature_reference_path,
    "w"
) as f:

    json.dump(
        feature_reference,
        f,
        indent=4
    )


print(
    "\nFeature reference saved:"
)

print(
    feature_reference_path
)


# ============================================================
# Save results
# ============================================================

results_path = os.path.join(
    RESULT_DIR,
    "cnn_lstm_results.txt"
)


with open(
    results_path,
    "w"
) as f:

    f.write(
        "CNN-LSTM Cyclone Prediction Results\n"
    )

    f.write(
        "====================================\n\n"
    )

    f.write(
        f"Accuracy : {accuracy:.4f}\n"
    )

    f.write(
        f"Precision: {precision:.4f}\n"
    )

    f.write(
        f"Recall   : {recall:.4f}\n"
    )

    f.write(
        f"F1       : {f1:.4f}\n"
    )

    f.write(
        f"ROC-AUC  : {roc_auc:.4f}\n"
    )

    f.write(
        f"PR-AUC   : {pr_auc:.4f}\n"
    )


# ============================================================
# Save predictions
# ============================================================

prediction_path = os.path.join(
    PREDICTION_DIR,
    "cnn_lstm_predictions.npz"
)


np.savez(
    prediction_path,

    y_test=y_test,

    y_pred_proba=y_pred_proba
)


# ============================================================
# Finished
# ============================================================

print("\n========================================")
print("SAVED FILES")
print("========================================")


print(
    "Training model:"
)

print(
    model_path
)


print(
    "\nDeployment model:"
)

print(
    artifact_model_path
)


print(
    "\nScaler:"
)

print(
    scaler_path
)


print(
    "\nFeature reference:"
)

print(
    feature_reference_path
)


print(
    "\nResults:"
)

print(
    results_path
)


print(
    "\nPredictions:"
)

print(
    prediction_path
)


print("\n========================================")
print("CNN-LSTM TRAINING COMPLETED")
print("========================================")

print(
    "\nCyclone deployment artifacts are ready."
)