# Phase 1: Data Preprocessing for Earthquake Prediction Project

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load the CSV file
data = pd.read_csv('../data/raw/data.csv', encoding='latin1')

if 'magnitude' not in data.columns:
    possible_names = ['Magnitude', 'MAGNITUDE', 'mag', 'Mag']
    for name in possible_names:
        if name in data.columns:
            data = data.rename(columns={name: 'magnitude'})
            print(f"Column name '{name}' renamed to 'magnitude'.")
            break
    else:
        raise KeyError("Column related to magnitude not found in the DataFrame.")

# Fill missing values using interpolation (numerical columns)
data['magnitude'] = data['magnitude'].interpolate()
data['depth'] = data['depth'].interpolate()

# NOTE: No region filter here — using global data intentionally, per project scope

# Check for missing values and clean data
print("Missing values before cleaning:")
print(data.isnull().sum())

# Drop rows with missing values in non-numerical columns
data = data.dropna(subset=['time', 'latitude', 'longitude', 'depth', 'magnitude', 'place'])
print("Missing values after cleaning:")
print(data.isnull().sum())

# Parse time BEFORE creating the significant-event label (need chronological order)
data['time'] = pd.to_datetime(data['time'], errors='coerce')
data = data.dropna(subset=['time'])
data = data.sort_values('time').reset_index(drop=True)

# Define the "significant event" target BEFORE normalizing magnitude
# (since normalizing would destroy the real-world magnitude scale we need for thresholding)
SIGNIFICANT_THRESHOLD = 5.5  # matches your project's "high" severity tier
data['significant'] = (data['magnitude'] >= SIGNIFICANT_THRESHOLD).astype(int)

print(f"\nSignificant events (M >= {SIGNIFICANT_THRESHOLD}): {data['significant'].sum()}")
print(f"Class distribution:\n{data['significant'].value_counts(normalize=True)}")

# Normalize magnitude and depth using MinMaxScaler (for model input features)
if data.empty:
    print("Warning: DataFrame is empty. Skipping scaling.")
else:
    scaler = MinMaxScaler()
    data[['magnitude_scaled', 'depth_scaled']] = scaler.fit_transform(data[['magnitude', 'depth']])
    print("Data normalized (kept original magnitude/depth alongside scaled versions).")

# Feature Engineering: Extract time-based features
data['year'] = data['time'].dt.year
data['month'] = data['time'].dt.month
data['day'] = data['time'].dt.day
data['hour'] = data['time'].dt.hour
print("Time-based features extracted.")

# Save preprocessed data to CSV
data.to_csv('../data/processed/preprocessed_earthquake_data.csv', index=False)
print("\nPreprocessed data saved to '../data/processed/preprocessed_earthquake_data.csv'.")
print(f"Total rows: {len(data)}")