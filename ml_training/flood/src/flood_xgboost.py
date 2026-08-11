import os
import numpy as np
import pandas as pd
import joblib

from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# FLOOD XGBOOST MODEL
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "flood_processed.csv"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "flood_scaler.pkl"
)

MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("Loading flood dataset...")

data = pd.read_csv(DATA_PATH)

target_column = "FloodProbability"

X = data.drop(columns=[target_column])
y = data[target_column]

print("Dataset shape:", data.shape)
print("Features:", X.shape)
print("Target:", y.shape)


# ============================================================
# LOAD SCALER
# ============================================================

print("Loading scaler...")

scaler = joblib.load(SCALER_PATH)

X_scaled = scaler.transform(X)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

split_index = int(len(X_scaled) * 0.8)

X_train = X_scaled[:split_index]
X_test = X_scaled[split_index:]

y_train = y.iloc[:split_index].values
y_test = y.iloc[split_index:].values


print("Training shape:", X_train.shape)
print("Testing shape:", X_test.shape)


# ============================================================
# BUILD XGBOOST MODEL
# ============================================================

print("\nBuilding XGBoost model...")

xgb_model = XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)

print("Training XGBoost...")


# ============================================================
# TRAIN
# ============================================================

xgb_model.fit(
    X_train,
    y_train
)

print("XGBoost training completed!")


# ============================================================
# PREDICTIONS
# ============================================================

print("\nEvaluating XGBoost...")

predictions = xgb_model.predict(X_test)


# ============================================================
# METRICS
# ============================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

r2 = r2_score(
    y_test,
    predictions
)


print("\nXGBoost Results:")
print(f"MAE  : {mae:.6f}")
print(f"RMSE : {rmse:.6f}")
print(f"R²   : {r2:.6f}")


# ============================================================
# SAVE MODEL
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "flood_baseline_xgb_notebook.json"
)

xgb_model.save_model(model_path)

print("\nXGBoost model saved successfully!")
print(model_path)