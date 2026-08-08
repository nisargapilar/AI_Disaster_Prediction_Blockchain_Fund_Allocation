import os
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)

from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier


# ============================================================
# Paths
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "cyclone_processed.csv"
)

MODEL_DIR = os.path.join(BASE_DIR, "models")
PREDICTION_DIR = os.path.join(BASE_DIR, "predictions")
RESULT_DIR = os.path.join(BASE_DIR, "results")


os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PREDICTION_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


# ============================================================
# Load dataset
# ============================================================

print("Loading processed cyclone dataset...")

data = pd.read_csv(DATA_PATH)

print(f"Rows loaded: {len(data)}")
print(f"Cyclones: {data['SID'].nunique()}")


# ============================================================
# Features
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
# Make sure data is sorted
# ============================================================

data["ISO_TIME"] = pd.to_datetime(
    data["ISO_TIME"],
    errors="coerce",
    utc=True
)

data = data.dropna(
    subset=["SID", "ISO_TIME"] + FEATURES + [TARGET]
)

data = data.sort_values(
    ["SID", "ISO_TIME"]
).reset_index(drop=True)


# ============================================================
# Split by cyclone
#
# IMPORTANT:
# We split complete cyclones rather than individual rows.
# This prevents the same cyclone from appearing in both
# training and testing.
# ============================================================

cyclone_ids = data["SID"].unique()

np.random.seed(42)
np.random.shuffle(cyclone_ids)

n_cyclones = len(cyclone_ids)

train_end = int(n_cyclones * 0.70)
val_end = int(n_cyclones * 0.85)

train_ids = cyclone_ids[:train_end]
val_ids = cyclone_ids[train_end:val_end]
test_ids = cyclone_ids[val_end:]


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
# Prepare X and y
# ============================================================

X_train = train_df[FEATURES].values
y_train = train_df[TARGET].astype(int).values

X_val = val_df[FEATURES].values
y_val = val_df[TARGET].astype(int).values

X_test = test_df[FEATURES].values
y_test = test_df[TARGET].astype(int).values


print("\nTraining class distribution:")
print(pd.Series(y_train).value_counts())


# ============================================================
# SMOTE
# ============================================================

print("\nApplying SMOTE to training data...")

smote = SMOTE(
    random_state=42,
    sampling_strategy=1.0
)

X_train_sm, y_train_sm = smote.fit_resample(
    X_train,
    y_train
)

print(f"Training rows after SMOTE: {X_train_sm.shape}")

print("Class distribution after SMOTE:")
print(pd.Series(y_train_sm).value_counts())


# ============================================================
# Build XGBoost model
# ============================================================

print("\nBuilding Baseline XGBoost...")

model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1,
)


# ============================================================
# Train
# ============================================================

print("Training Baseline XGBoost...")

model.fit(
    X_train_sm,
    y_train_sm,
    eval_set=[(X_val, y_val)],
    verbose=False
)


# ============================================================
# Test predictions
# ============================================================

print("\nGenerating test predictions...")

y_pred_proba = model.predict_proba(X_test)[:, 1]

y_pred = (y_pred_proba >= 0.5).astype(int)


# ============================================================
# Metrics
# ============================================================

accuracy = accuracy_score(y_test, y_pred)

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


print("\n=== Baseline XGBoost Results ===")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1       : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")
print(f"PR-AUC   : {pr_auc:.4f}")


# ============================================================
# Save model
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "cyclone_baseline_xgb.json"
)

model.save_model(model_path)


# ============================================================
# Save results
# ============================================================

results_path = os.path.join(
    RESULT_DIR,
    "baseline_xgb_results.txt"
)

with open(results_path, "w") as f:
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Precision: {precision:.4f}\n")
    f.write(f"Recall: {recall:.4f}\n")
    f.write(f"F1: {f1:.4f}\n")
    f.write(f"ROC-AUC: {roc_auc:.4f}\n")
    f.write(f"PR-AUC: {pr_auc:.4f}\n")


# ============================================================
# Save predictions
#
# This is required by compare_models.py
# ============================================================

prediction_path = os.path.join(
    PREDICTION_DIR,
    "baseline_xgb_predictions.npz"
)

np.savez(
    prediction_path,
    y_test=y_test,
    y_pred_proba=y_pred_proba
)


print("\nSaved files:")

print("Model       :", model_path)
print("Results     :", results_path)
print("Predictions :", prediction_path)

print("\nNext model: CNN-LSTM")