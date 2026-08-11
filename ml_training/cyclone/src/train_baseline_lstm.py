# ============================================================
# Baseline LSTM — Cyclone Intensification Prediction
# ============================================================

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
    confusion_matrix
)

from imblearn.over_sampling import SMOTE

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2

import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. REPRODUCIBILITY
# ============================================================

np.random.seed(42)
random.seed(42)
tf.random.set_seed(42)


# ============================================================
# 2. PATHS
# ============================================================

DATA_FILE = "cyclone/data/processed/cyclone_processed.csv"

MODEL_DIR = "cyclone/models"
RESULTS_DIR = "cyclone/results"
FIGURES_DIR = "cyclone/results/figures"
PREDICTIONS_DIR = "cyclone/predictions"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(PREDICTIONS_DIR, exist_ok=True)


# ============================================================
# 3. LOAD DATA
# ============================================================

print("Loading processed cyclone dataset...")

data = pd.read_csv(DATA_FILE)

data["ISO_TIME"] = pd.to_datetime(
    data["ISO_TIME"],
    errors="coerce",
    utc=True
)

data = data.dropna(
    subset=["ISO_TIME"]
)

data = data.sort_values(
    ["SID", "ISO_TIME"]
).reset_index(drop=True)

print(f"Rows loaded: {len(data)}")
print(f"Cyclones: {data['SID'].nunique()}")


# ============================================================
# 4. FEATURES AND TARGET
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
    "hour"
]

TARGET = "intensifies"


# ============================================================
# 5. CHRONOLOGICAL SPLIT
#
# 70% train
# 15% validation
# 15% test
#
# Split is based on cyclone IDs so observations from the
# same cyclone are not spread across train/test.
# ============================================================

cyclone_ids = (
    data["SID"]
    .drop_duplicates()
    .tolist()
)

n_cyclones = len(cyclone_ids)

train_end = int(n_cyclones * 0.70)
val_end = int(n_cyclones * 0.85)

train_ids = cyclone_ids[:train_end]
val_ids = cyclone_ids[train_end:val_end]
test_ids = cyclone_ids[val_end:]

train_df = data[
    data["SID"].isin(train_ids)
].copy()

val_df = data[
    data["SID"].isin(val_ids)
].copy()

test_df = data[
    data["SID"].isin(test_ids)
].copy()

print("\nDataset split:")
print(f"Train cyclones: {len(train_ids)}")
print(f"Validation cyclones: {len(val_ids)}")
print(f"Test cyclones: {len(test_ids)}")

print(f"\nTrain rows: {len(train_df)}")
print(f"Validation rows: {len(val_df)}")
print(f"Test rows: {len(test_df)}")


# ============================================================
# 6. SCALE FEATURES
#
# Fit scaler ONLY on training data.
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
# 7. CREATE SEQUENCES
#
# Each sequence contains 12 observations from the SAME cyclone.
#
# Sequence:
# t-11 ... t-10 ... ... t-1
#
# Target:
# intensification at t
# ============================================================

SEQUENCE_LENGTH = 12


def create_sequences(df):

    X = []
    y = []

    for sid, group in df.groupby("SID"):

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
        np.asarray(X, dtype=np.float32),
        np.asarray(y, dtype=np.int32)
    )


X_train, y_train = create_sequences(
    train_df
)

X_val, y_val = create_sequences(
    val_df
)

X_test, y_test = create_sequences(
    test_df
)


print("\nSequence shapes:")
print("X_train:", X_train.shape)
print("y_train:", y_train.shape)
print("X_val:", X_val.shape)
print("y_val:", y_val.shape)
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ============================================================
# 8. CHECK CLASS DISTRIBUTION
# ============================================================

print("\nTraining class distribution:")

print(
    pd.Series(y_train)
    .value_counts()
)


# ============================================================
# 9. SMOTE
#
# LSTM sequences are temporarily flattened for SMOTE.
# They are reshaped back afterwards.
# ============================================================

print("\nApplying SMOTE to training sequences...")

X_train_flat = X_train.reshape(
    X_train.shape[0],
    -1
)

smote = SMOTE(
    random_state=42,
    sampling_strategy=1.0
)

X_train_smote, y_train_smote = (
    smote.fit_resample(
        X_train_flat,
        y_train
    )
)

X_train_smote = X_train_smote.reshape(
    -1,
    SEQUENCE_LENGTH,
    len(FEATURES)
)

print(
    "Training sequences after SMOTE:",
    X_train_smote.shape
)

print(
    "Class distribution after SMOTE:"
)

print(
    pd.Series(y_train_smote)
    .value_counts()
)


# ============================================================
# 10. BUILD BASELINE LSTM
#
# This is intentionally a plain LSTM.
# No CNN / Conv1D.
# ============================================================

print("\nBuilding Baseline LSTM...")

model = Sequential([
    LSTM(
        32,
        input_shape=(
            SEQUENCE_LENGTH,
            len(FEATURES)
        )
    ),

    Dense(
        16,
        activation="relu",
        kernel_regularizer=l2(0.001)
    ),

    Dropout(0.3),

    Dense(
        1,
        activation="sigmoid"
    )
])


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
# 11. TRAIN
# ============================================================

early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)


print("\nTraining Baseline LSTM...")

history = model.fit(
    X_train_smote,
    y_train_smote,

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
# 12. PREDICTION
# ============================================================

print("\nGenerating test predictions...")

y_pred_proba = (
    model.predict(
        X_test,
        verbose=0
    )
    .ravel()
)

y_pred = (
    y_pred_proba >= 0.5
).astype(int)


# ============================================================
# 13. METRICS
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


print("\n========================================")
print("BASELINE LSTM RESULTS")
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
# 14. CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_test,
    y_pred
)

plt.figure(
    figsize=(6, 5)
)

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    cbar=False
)

plt.title(
    "Confusion Matrix — Baseline LSTM"
)

plt.xlabel(
    "Predicted"
)

plt.ylabel(
    "Actual"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIGURES_DIR,
        "confusion_matrix_baseline_lstm.png"
    ),
    dpi=150
)

plt.close()


# ============================================================
# 15. TRAINING CURVES
# ============================================================

plt.figure(
    figsize=(8, 5)
)

plt.plot(
    history.history["loss"],
    label="Training Loss"
)

plt.plot(
    history.history["val_loss"],
    label="Validation Loss"
)

plt.title(
    "Baseline LSTM Training Loss"
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Loss"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIGURES_DIR,
        "baseline_lstm_training_loss.png"
    ),
    dpi=150
)

plt.close()


# ============================================================
# 16. SAVE MODEL
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "cyclone_baseline_lstm.keras"
)

model.save(
    model_path
)


# ============================================================
# 17. SAVE RESULTS
# ============================================================

results_file = os.path.join(
    RESULTS_DIR,
    "baseline_lstm_results.txt"
)

with open(
    results_file,
    "w"
) as f:

    f.write(
        "Baseline LSTM — Cyclone Intensification\n"
    )

    f.write(
        "========================================\n"
    )

    f.write(
        f"Accuracy: {accuracy:.4f}\n"
    )

    f.write(
        f"Precision: {precision:.4f}\n"
    )

    f.write(
        f"Recall: {recall:.4f}\n"
    )

    f.write(
        f"F1: {f1:.4f}\n"
    )

    f.write(
        f"ROC-AUC: {roc_auc:.4f}\n"
    )

    f.write(
        f"PR-AUC: {pr_auc:.4f}\n"
    )


# ============================================================
# 18. SAVE PREDICTIONS
#
# compare_models.py will use this file later.
# ============================================================

prediction_file = os.path.join(
    PREDICTIONS_DIR,
    "baseline_lstm_predictions.npz"
)

np.savez(
    prediction_file,
    y_test=y_test,
    y_pred_proba=y_pred_proba
)


# ============================================================
# 19. FINISHED
# ============================================================

print("\n========================================")
print("BASELINE LSTM COMPLETE")
print("========================================")

print("\nSaved files:")

print(
    f"Model       : {model_path}"
)

print(
    f"Results     : {results_file}"
)

print(
    f"Predictions : {prediction_file}"
)

print(
    "\nNext model: Baseline XGBoost"
)