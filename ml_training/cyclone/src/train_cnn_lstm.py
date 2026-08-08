import os
import random
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
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, LSTM, Dense, Dropout
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
# Paths
# ============================================================

DATA_PATH = "cyclone/data/processed/cyclone_processed.csv"

MODEL_DIR = "cyclone/models"
RESULT_DIR = "cyclone/results"
PREDICTION_DIR = "cyclone/predictions"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(PREDICTION_DIR, exist_ok=True)


# ============================================================
# Load dataset
# ============================================================

print("Loading processed cyclone dataset...")

data = pd.read_csv(DATA_PATH)

print(f"Rows loaded: {len(data)}")
print(f"Cyclones: {data['SID'].nunique()}")


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
    data[col] = pd.to_numeric(data[col], errors="coerce")

data[TARGET] = pd.to_numeric(data[TARGET], errors="coerce")

data = data.dropna(
    subset=FEATURES + [TARGET]
).copy()

data = data.sort_values(
    ["SID", "ISO_TIME"]
).reset_index(drop=True)

print(f"Rows after final cleaning: {len(data)}")
print(f"Cyclones after final cleaning: {data['SID'].nunique()}")


# ============================================================
# Split by cyclone
# IMPORTANT:
# A cyclone must belong to only one split.
# ============================================================

cyclones = data["SID"].unique()

rng = np.random.default_rng(SEED)
rng.shuffle(cyclones)

n_cyclones = len(cyclones)

train_end = int(n_cyclones * 0.70)
val_end = int(n_cyclones * 0.85)

train_ids = cyclones[:train_end]
val_ids = cyclones[train_end:val_end]
test_ids = cyclones[val_end:]


train_df = data[data["SID"].isin(train_ids)].copy()
val_df = data[data["SID"].isin(val_ids)].copy()
test_df = data[data["SID"].isin(test_ids)].copy()

print("\nDataset split:")
print(f"Train cyclones: {len(train_ids)}")
print(f"Validation cyclones: {len(val_ids)}")
print(f"Test cyclones: {len(test_ids)}")

print(f"Train rows: {len(train_df)}")
print(f"Validation rows: {len(val_df)}")
print(f"Test rows: {len(test_df)}")


# ============================================================
# Scale features
# Fit ONLY on training data
# ============================================================

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

    for sid, group in df.groupby("SID"):

        group = group.sort_values("ISO_TIME")

        feature_values = group[FEATURES].values
        target_values = group[TARGET].values

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

    return np.array(X, dtype=np.float32), np.array(
        y, dtype=np.int32
    )


X_train, y_train = make_sequences(train_df)
X_val, y_val = make_sequences(val_df)
X_test, y_test = make_sequences(test_df)


print("\nSequence shapes:")
print("X_train:", X_train.shape)
print("y_train:", y_train.shape)
print("X_val:", X_val.shape)
print("y_val:", y_val.shape)
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ============================================================
# Training class distribution
# ============================================================

print("\nTraining class distribution:")
print(pd.Series(y_train).value_counts())


# ============================================================
# SMOTE
#
# SMOTE works on 2D data, so flatten the sequence first.
# Then reshape it back to 3D.
# ============================================================

print("\nApplying SMOTE to training sequences...")

X_train_flat = X_train.reshape(
    X_train.shape[0],
    -1
)

smote = SMOTE(
    random_state=SEED,
    sampling_strategy=1.0
)

X_train_sm, y_train_sm = smote.fit_resample(
    X_train_flat,
    y_train
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

print("Class distribution after SMOTE:")
print(pd.Series(y_train_sm).value_counts())


# ============================================================
# Build CNN-LSTM
# ============================================================

print("\nBuilding CNN-LSTM model...")

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


model.compile(
    optimizer=Adam(
        learning_rate=0.001
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy"
    ]
)


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

print("\nTraining CNN-LSTM...")

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

print("\nGenerating test predictions...")

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

print("\n=== CNN-LSTM Results ===")

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
# Save model
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "cyclone_cnn_lstm.keras"
)

model.save(
    model_path
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
#
# compare_models.py expects exactly these keys:
# y_test
# y_pred_proba
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

print("\nSaved files:")

print(
    "Model       :",
    model_path
)

print(
    "Results     :",
    results_path
)

print(
    "Predictions :",
    prediction_path
)

print(
    "\nCNN-LSTM training completed successfully."
)

print(
    "Next step: run the cyclone comparison script."
)