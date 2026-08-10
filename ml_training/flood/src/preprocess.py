import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import joblib

# ==========================================
# 1. Load the raw flood dataset
# ==========================================

INPUT_PATH = "data/raw/flood.csv"
OUTPUT_PATH = "data/processed/flood_processed.csv"
SCALER_PATH = "data/processed/flood_scaler.pkl"
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
    raise KeyError(f"Target column '{TARGET}' not found.")

X = data.drop(columns=[TARGET])
y = data[TARGET]

print("\nFeature shape:", X.shape)
print("Target shape:", y.shape)


# ==========================================
# 5. Normalize input features
# ==========================================

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
# 7. Save scaler
# ==========================================

joblib.dump(scaler, SCALER_PATH)

print(f"\nScaler saved to: {SCALER_PATH}")


# ==========================================
# 8. Save processed dataset
# ==========================================

processed_data.to_csv(
    OUTPUT_PATH,
    index=False
)

print(f"Processed dataset saved to: {OUTPUT_PATH}")
print(f"Final dataset shape: {processed_data.shape}")


# ==========================================
# 9. Display sample
# ==========================================

print("\nFirst 5 processed rows:")
print(processed_data.head())

print("\nFloodProbability statistics:")
print(processed_data[TARGET].describe())

print("\nPreprocessing completed successfully!")