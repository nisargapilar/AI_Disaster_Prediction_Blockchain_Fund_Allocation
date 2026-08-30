import os
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib


# ==========================================
# PATHS
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INPUT_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "flood.csv"
)

OUTPUT_PATH = os.path.join(
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


# ==========================================
# 1. Load the raw flood dataset
# ==========================================

print("Loading flood dataset...")

data = pd.read_csv(INPUT_PATH)

print(f"Original dataset shape: {data.shape}")

print("\nColumns:")
print(data.columns.tolist())


# ==========================================
# 2. Check missing values
# ==========================================

print("\nMissing values before cleaning:")
print(data.isnull().sum())


# ==========================================
# 3. Remove rows with missing values
# ==========================================

data = data.dropna().reset_index(drop=True)

print("\nMissing values after cleaning:")
print(data.isnull().sum())


# ==========================================
# 4. Separate features and target
# ==========================================

TARGET = "FloodProbability"

if TARGET not in data.columns:
    raise KeyError(
        f"Target column '{TARGET}' not found."
    )

X = data.drop(
    columns=[TARGET]
)

y = data[TARGET]

print("\nFeature shape:", X.shape)
print("Target shape:", y.shape)

print("\nFeatures:")
print(X.columns.tolist())


# ==========================================
# 5. Normalize input features
# ==========================================

print("\nCreating MinMaxScaler...")

scaler = MinMaxScaler()

X_scaled = scaler.fit_transform(X)

X_scaled = pd.DataFrame(
    X_scaled,
    columns=X.columns
)


# ==========================================
# 6. Add target column back
# ==========================================

processed_data = X_scaled.copy()

processed_data[TARGET] = y.values


# ==========================================
# 7. Create processed directory
# ==========================================

os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)


# ==========================================
# 8. Save scaler
# ==========================================

print("\nSaving scaler...")

joblib.dump(
    scaler,
    SCALER_PATH
)

print(f"Scaler saved to:")
print(SCALER_PATH)


# ==========================================
# 9. Save processed dataset
# ==========================================

print("\nSaving processed dataset...")

processed_data.to_csv(
    OUTPUT_PATH,
    index=False
)

print(f"Processed dataset saved to:")
print(OUTPUT_PATH)

print(
    f"Final dataset shape: {processed_data.shape}"
)


# ==========================================
# 10. Display sample
# ==========================================

print("\nFirst 5 processed rows:")
print(processed_data.head())


# ==========================================
# 11. FloodProbability statistics
# ==========================================

print("\nFloodProbability statistics:")
print(
    processed_data[TARGET].describe()
)


# ==========================================
# 12. Final information
# ==========================================

print("\n==========================================")
print("PREPROCESSING COMPLETED SUCCESSFULLY")
print("==========================================")

print(f"Input rows      : {len(data)}")
print(f"Input features  : {X.shape[1]}")
print(f"Output features : {X_scaled.shape[1]}")
print(f"Target          : {TARGET}")
print(f"Scaler          : {SCALER_PATH}")
print(f"Processed data  : {OUTPUT_PATH}")