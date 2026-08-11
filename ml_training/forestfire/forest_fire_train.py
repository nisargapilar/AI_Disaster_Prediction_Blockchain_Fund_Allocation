import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# ===========================
# Load Dataset (confirmed FIRMS detections - MODIS, India)
# ===========================
df_archive = pd.read_csv("fire_archive_M6_107977.csv")
df_nrt = pd.read_csv("fire_nrt_M6_107977.csv")
df = pd.concat([df_archive, df_nrt], ignore_index=True)

print(f"Total confirmed detections loaded: {len(df)}")

# ===========================
# Derive severity_tier from frp (fire radiative power)
# 3 tiers instead of 4 - removes the fuzziest boundary
# ===========================
quantiles = df["frp"].quantile([1/3, 2/3]).values

def frp_to_tier(frp):
    if frp <= quantiles[0]:
        return "low"
    elif frp <= quantiles[1]:
        return "medium"
    else:
        return "high"

df["severity_tier"] = df["frp"].apply(frp_to_tier)

print("\nSeverity tier distribution:")
print(df["severity_tier"].value_counts())

# ===========================
# Features & Target
# ===========================
df["daynight_encoded"] = df["daynight"].map({"D": 1, "N": 0})

df["acq_date"] = pd.to_datetime(df["acq_date"])
df["month"] = df["acq_date"].dt.month
df["day_of_year"] = df["acq_date"].dt.dayofyear

feature_cols = ["latitude", "longitude", "brightness", "scan", "track",
                 "confidence", "bright_t31", "daynight_encoded",
                 "month", "day_of_year", "type"]

X = df[feature_cols]
y = df["severity_tier"]

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# ===========================
# Split Dataset
# ===========================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

# ===========================
# Train Model (XGBoost multiclass)
# ===========================
model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="multi:softprob",
    num_class=len(label_encoder.classes_),
    eval_metric="mlogloss",
    random_state=42
)
model.fit(X_train, y_train)

# ===========================
# Predictions
# ===========================
y_pred = model.predict(X_test)

# ===========================
# Metrics
# ===========================
accuracy = accuracy_score(y_test, y_pred)
print("\n" + "=" * 50)
print(f"Accuracy : {accuracy:.2%}")
print("=" * 50)
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# ===========================
# Example prediction
# ===========================
sample = pd.DataFrame([{
    "latitude": 22.5,
    "longitude": 78.9,
    "brightness": 340.0,
    "scan": 1.2,
    "track": 1.1,
    "confidence": 80,
    "bright_t31": 295.0,
    "daynight_encoded": 1,
    "month": 4,
    "day_of_year": 105,
    "type": 0
}])
sample_pred = model.predict(sample)
sample_tier = label_encoder.inverse_transform(sample_pred)[0]
print(f"\nExample severity_tier for sample confirmed detection: {sample_tier}")

# ===========================
# Save Model
# ===========================
joblib.dump(model, "fire_severity_xgb_model.pkl")
joblib.dump(label_encoder, "severity_label_encoder.pkl")
joblib.dump(feature_cols, "feature_columns.pkl")
print("\n✅ Model saved as fire_severity_xgb_model.pkl")
print("✅ Label encoder saved as severity_label_encoder.pkl")
print("✅ Feature list saved as feature_columns.pkl")