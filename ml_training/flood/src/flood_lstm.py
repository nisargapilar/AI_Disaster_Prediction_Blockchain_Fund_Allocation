import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dropout, Dense
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# FLOOD LSTM MODEL
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

print("Input range:")
print(X_scaled.min(), "to", X_scaled.max())


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

split_index = int(len(X_scaled) * 0.8)

X_train = X_scaled[:split_index]
X_test = X_scaled[split_index:]

y_train = y.iloc[:split_index].values
y_test = y.iloc[split_index:].values


# ============================================================
# RESHAPE FOR LSTM
# ============================================================

X_train_lstm = X_train.reshape(
    X_train.shape[0],
    X_train.shape[1],
    1
)

X_test_lstm = X_test.reshape(
    X_test.shape[0],
    X_test.shape[1],
    1
)

print("LSTM training shape:", X_train_lstm.shape)
print("LSTM testing shape:", X_test_lstm.shape)

print("LSTM target training shape:", y_train.shape)
print("LSTM target testing shape:", y_test.shape)


# ============================================================
# BUILD LSTM MODEL
# ============================================================

print("Building LSTM model...")

lstm_model = Sequential([
    Input(shape=(X_train_lstm.shape[1], 1)),

    LSTM(64),

    Dropout(0.2),

    Dense(32, activation="relu"),

    Dense(1)
])


lstm_model.compile(
    optimizer="adam",
    loss="mse",
    metrics=["mae"]
)

lstm_model.summary()


# ============================================================
# TRAIN LSTM
# ============================================================

print("Training LSTM...")

history = lstm_model.fit(
    X_train_lstm,
    y_train,
    epochs=20,
    batch_size=64,
    validation_split=0.2,
    verbose=1
)

print("LSTM training completed!")


# ============================================================
# EVALUATE
# ============================================================

print("Evaluating LSTM...")

predictions = lstm_model.predict(
    X_test_lstm,
    verbose=0
).flatten()

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

print("\nLSTM Results:")
print(f"MAE  : {mae:.6f}")
print(f"RMSE : {rmse:.6f}")
print(f"R²   : {r2:.6f}")


# ============================================================
# SAVE MODEL
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "flood_corrected_lstm.keras"
)

lstm_model.save(model_path)

print("\nLSTM model saved successfully!")
print(model_path)