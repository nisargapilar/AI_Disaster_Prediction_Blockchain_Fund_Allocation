# ============================================================
# Phase 1: Cyclone Data Preprocessing
# IBTrACS North Indian Ocean (NI)
#
# Project:
# AI Disaster Prediction + Blockchain Fund Allocation
#
# Target:
# 1 = cyclone intensifies at the next observation
# 0 = cyclone does not intensify
# ============================================================

import os
import pandas as pd
import numpy as np


# ============================================================
# 1. PATHS
# ============================================================

RAW_FILE = "cyclone/data/raw/ibtracs.NI.list.v04r01.csv"

PROCESSED_DIR = "cyclone/data/processed"

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "cyclone_processed.csv"
)

# Create processed folder if it does not exist
os.makedirs(PROCESSED_DIR, exist_ok=True)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("========================================")
print("CYCLONE DATA PREPROCESSING")
print("========================================")

print("\nLoading IBTrACS dataset...")

data = pd.read_csv(
    RAW_FILE,
    skiprows=[1],
    low_memory=False
)

print(f"Raw rows: {len(data)}")
print(f"Raw columns: {len(data.columns)}")


# ============================================================
# 3. SELECT REQUIRED COLUMNS
# ============================================================

required_columns = [
    "SID",
    "SEASON",
    "NAME",
    "ISO_TIME",
    "LAT",
    "LON",
    "WMO_WIND",
    "WMO_PRES",
    "NEWDELHI_WIND",
    "NEWDELHI_PRES",
    "STORM_SPEED",
    "STORM_DIR",
    "DIST2LAND"
]

# Check that all required columns exist
missing_columns = [
    col for col in required_columns
    if col not in data.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in dataset: {missing_columns}"
    )

data = data[required_columns].copy()

print("\nRequired columns selected.")


# ============================================================
# 4. CONVERT EMPTY STRINGS TO NaN
# ============================================================

data = data.replace(
    r"^\s*$",
    np.nan,
    regex=True
)


# ============================================================
# 5. CONVERT NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "LAT",
    "LON",
    "WMO_WIND",
    "WMO_PRES",
    "NEWDELHI_WIND",
    "NEWDELHI_PRES",
    "STORM_SPEED",
    "STORM_DIR",
    "DIST2LAND"
]

for column in numeric_columns:
    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )


# ============================================================
# 6. CONVERT TIME
# ============================================================

data["ISO_TIME"] = pd.to_datetime(
    data["ISO_TIME"],
    errors="coerce",
    utc=True
)


# ============================================================
# 7. REMOVE INVALID ESSENTIAL ROWS
# ============================================================

print("\nMissing values before cleaning:")

print(
    data[
        [
            "SID",
            "ISO_TIME",
            "LAT",
            "LON",
            "WMO_WIND"
        ]
    ].isna().sum()
)

data = data.dropna(
    subset=[
        "SID",
        "ISO_TIME",
        "LAT",
        "LON",
        "WMO_WIND"
    ]
)


# ============================================================
# 8. SORT BY CYCLONE AND TIME
# ============================================================

data = data.sort_values(
    ["SID", "ISO_TIME"]
).reset_index(drop=True)


print(f"\nRows after cleaning: {len(data)}")

print(
    f"Number of individual cyclones: "
    f"{data['SID'].nunique()}"
)


# ============================================================
# 9. TIME FEATURES
# ============================================================

data["year"] = data["ISO_TIME"].dt.year
data["month"] = data["ISO_TIME"].dt.month
data["day"] = data["ISO_TIME"].dt.day
data["hour"] = data["ISO_TIME"].dt.hour


# ============================================================
# 10. PREVIOUS WIND
#
# Calculated separately for each cyclone.
# ============================================================

data["previous_wind"] = (
    data
    .groupby("SID")["WMO_WIND"]
    .shift(1)
)


# ============================================================
# 11. NEXT WIND
#
# This is used ONLY to create the target.
# It is NOT used as an input feature.
# ============================================================

data["next_wind"] = (
    data
    .groupby("SID")["WMO_WIND"]
    .shift(-1)
)


# ============================================================
# 12. REMOVE LAST OBSERVATION OF EACH CYCLONE
#
# The last observation has no next_wind,
# therefore it cannot have a prediction target.
# ============================================================

data = data.dropna(
    subset=["next_wind"]
).reset_index(drop=True)


# ============================================================
# 13. CREATE WIND CHANGE FEATURE
# ============================================================

data["wind_change"] = (
    data["WMO_WIND"] -
    data["previous_wind"]
)

data["wind_change"] = data["wind_change"].fillna(0)


# ============================================================
# 14. CREATE TARGET
#
# 1 = next wind is greater than current wind
# 0 = next wind is same or lower
# ============================================================

data["intensifies"] = (
    data["next_wind"] >
    data["WMO_WIND"]
).astype(int)


# ============================================================
# 15. TARGET DISTRIBUTION
# ============================================================

print("\n========================================")
print("TARGET DISTRIBUTION")
print("========================================")

target_counts = data["intensifies"].value_counts()

print(
    target_counts.rename(
        index={
            0: "Does NOT intensify",
            1: "Intensifies"
        }
    )
)

print("\nTarget percentage:")

target_percent = (
    data["intensifies"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

print(
    target_percent.rename(
        index={
            0: "Does NOT intensify",
            1: "Intensifies"
        }
    )
)


# ============================================================
# 16. MODEL FEATURES
# ============================================================

feature_columns = [
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


# ============================================================
# 17. HANDLE MISSING FEATURE VALUES
#
# IMPORTANT:
# We do NOT fill the target.
# Only model input features are filled.
# ============================================================

print("\nMissing values in model features:")

print(
    data[feature_columns]
    .isna()
    .sum()
)


for column in feature_columns:

    if data[column].isna().any():

        median_value = data[column].median()

        data[column] = data[column].fillna(
            median_value
        )


# ============================================================
# 18. FINAL DATASET
#
# Keep SID because the LSTM will use it to create
# sequences without mixing different cyclones.
# ============================================================

output_columns = [
    "SID",
    "SEASON",
    "NAME",
    "ISO_TIME"
] + feature_columns + [
    "intensifies"
]

data = data[output_columns]


# ============================================================
# 19. FINAL VALIDATION
# ============================================================

print("\n========================================")
print("FINAL DATASET CHECK")
print("========================================")

print(f"Rows: {len(data)}")

print(
    f"Unique cyclones: "
    f"{data['SID'].nunique()}"
)

print(
    f"Date range: "
    f"{data['ISO_TIME'].min()} "
    f"to "
    f"{data['ISO_TIME'].max()}"
)

print("\nRemaining missing values:")

print(
    data.isna().sum()
)


# ============================================================
# 20. SAVE PROCESSED DATA
# ============================================================

data.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 21. FINISH
# ============================================================

print("\n========================================")
print("PREPROCESSING COMPLETE")
print("========================================")

print(
    f"\nProcessed dataset saved to:"
)

print(
    f"  {OUTPUT_FILE}"
)

print("\nFeatures used by the models:")

for feature in feature_columns:
    print(
        f"  - {feature}"
    )

print("\nTarget:")

print(
    "  intensifies = 1 -> "
    "next observation has higher wind"
)

print(
    "  intensifies = 0 -> "
    "next observation has same/lower wind"
)

print("\nReady for the three models:")
print("  1. CNN-LSTM")
print("  2. Baseline LSTM")
print("  3. Baseline XGBoost")