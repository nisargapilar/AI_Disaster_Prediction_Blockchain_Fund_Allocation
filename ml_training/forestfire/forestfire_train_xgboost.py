import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# 1. LOAD DATASET
# ============================================================

df_archive = pd.read_csv("data/raw/fire_archive_M6_107977.csv")
df_nrt = pd.read_csv("data/raw/fire_nrt_M6_107977.csv")

df = pd.concat(
    [df_archive, df_nrt],
    ignore_index=True
)

print(f"Total confirmed detections loaded: {len(df)}")


# ============================================================
# 2. CREATE SEVERITY TIER FROM FRP
# ============================================================

quantiles = df["frp"].quantile([1/3, 2/3]).values

print("\nFRP thresholds:")
print(f"Low/Medium threshold  : {quantiles[0]:.4f}")
print(f"Medium/High threshold : {quantiles[1]:.4f}")


def frp_to_tier(frp):

    if frp <= quantiles[0]:
        return "low"

    elif frp <= quantiles[1]:
        return "medium"

    else:
        return "high"


df["severity_tier"] = df["frp"].apply(
    frp_to_tier
)


print("\nSeverity Tier Distribution:")
print(
    df["severity_tier"].value_counts()
)


# ============================================================
# 3. FEATURE ENGINEERING
# ============================================================

# Day/Night encoding

df["daynight_encoded"] = df["daynight"].map({
    "D": 1,
    "N": 0
})


# Date conversion

df["acq_date"] = pd.to_datetime(
    df["acq_date"],
    errors="coerce"
)


# Extract date features

df["month"] = df["acq_date"].dt.month

df["day_of_year"] = (
    df["acq_date"].dt.dayofyear
)


# ============================================================
# 4. FEATURES
# ============================================================

feature_cols = [

    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "confidence",
    "bright_t31",
    "daynight_encoded",
    "month",
    "day_of_year",
    "type"

]


X = df[feature_cols].copy()

y = df["severity_tier"]


# ============================================================
# 5. CHECK MISSING VALUES
# ============================================================

print("\nMissing values:")

print(
    X.isnull().sum()
)


# ============================================================
# 6. HANDLE MISSING VALUES
# ============================================================

imputer = SimpleImputer(
    strategy="median"
)

X = pd.DataFrame(
    imputer.fit_transform(X),
    columns=feature_cols
)


print(
    "\nTotal remaining missing values:",
    X.isnull().sum().sum()
)


# ============================================================
# 7. ENCODE TARGET
# ============================================================

label_encoder = LabelEncoder()

y_encoded = label_encoder.fit_transform(y)


print("\nClasses:")

print(
    label_encoder.classes_
)


# ============================================================
# 8. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y_encoded,

    test_size=0.20,

    random_state=42,

    stratify=y_encoded

)


print("\nTraining samples:", len(X_train))

print("Testing samples :", len(X_test))


# ============================================================
# 9. XGBOOST MODEL
# ORIGINAL BEST CONFIGURATION
# ============================================================

model = XGBClassifier(

    n_estimators=300,

    max_depth=6,

    learning_rate=0.1,

    subsample=0.9,

    colsample_bytree=0.9,

    objective="multi:softprob",

    num_class=len(
        label_encoder.classes_
    ),

    eval_metric="mlogloss",

    random_state=42,

    n_jobs=-1

)


print("\n" + "=" * 60)

print("Training XGBoost...")

print("=" * 60)


# ============================================================
# 10. TRAIN
# ============================================================

model.fit(
    X_train,
    y_train
)


print("\nTraining completed!")


# ============================================================
# 11. PREDICTIONS
# ============================================================

y_pred = model.predict(
    X_test
)


# ============================================================
# 12. ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)


print("\n" + "=" * 60)

print("XGBOOST RESULTS")

print("=" * 60)

print(
    f"\nAccuracy : {accuracy:.4%}"
)


# ============================================================
# 13. CLASSIFICATION REPORT
# ============================================================

print(
    "\nClassification Report:\n"
)

print(
    classification_report(

        y_test,

        y_pred,

        target_names=
        label_encoder.classes_,

        digits=4

    )
)


# ============================================================
# 14. CONFUSION MATRIX
# ============================================================

print(
    "\nConfusion Matrix:\n"
)

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


# ============================================================
# 15. FEATURE IMPORTANCE
# ============================================================

feature_importance = pd.DataFrame({

    "Feature": feature_cols,

    "Importance":
        model.feature_importances_

})


feature_importance = (
    feature_importance
    .sort_values(
        by="Importance",
        ascending=False
    )
)


print(
    "\nFeature Importance:\n"
)

print(
    feature_importance.to_string(
        index=False
    )
)


# ============================================================
# 16. EXAMPLE PREDICTION
# ============================================================

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


# Apply same imputation

sample = pd.DataFrame(

    imputer.transform(sample),

    columns=feature_cols

)


sample_pred = model.predict(
    sample
)


sample_tier = (
    label_encoder
    .inverse_transform(
        sample_pred
    )[0]
)


print(
    f"\nExample severity_tier: "
    f"{sample_tier}"
)


# ============================================================
# 17. SAVE PRODUCTION ARTIFACTS
# ============================================================

import os
import json

# ------------------------------------------------------------
# FIND PROJECT ROOT
# ------------------------------------------------------------
# Current file:
# PROJECT_ROOT/ml_training/forestfire/forestfire_train_xgboost.py
#
# Therefore:
# forestfire -> ml_training -> PROJECT_ROOT

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

ARTIFACT_DIR = os.path.join(
    PROJECT_ROOT,
    "backend",
    "ml_artifacts",
    "forestfire_artifacts"
)

os.makedirs(
    ARTIFACT_DIR,
    exist_ok=True
)

print("\n" + "=" * 60)
print("SAVING FOREST FIRE PRODUCTION ARTIFACTS")
print("=" * 60)

print("\nArtifact directory:")
print(ARTIFACT_DIR)


# ============================================================
# SAVE XGBOOST MODEL
# ============================================================

MODEL_PATH = os.path.join(
    ARTIFACT_DIR,
    "forestfire_xgboost.pkl"
)

joblib.dump(
    model,
    MODEL_PATH
)


# ============================================================
# SAVE LABEL ENCODER
# ============================================================

LABEL_ENCODER_PATH = os.path.join(
    ARTIFACT_DIR,
    "forestfire_label_encoder.pkl"
)

joblib.dump(
    label_encoder,
    LABEL_ENCODER_PATH
)


# ============================================================
# SAVE IMPUTER
# ============================================================

IMPUTER_PATH = os.path.join(
    ARTIFACT_DIR,
    "forestfire_imputer.pkl"
)

joblib.dump(
    imputer,
    IMPUTER_PATH
)


# ============================================================
# SAVE FEATURE REFERENCE
# ============================================================

FEATURE_REF_PATH = os.path.join(
    ARTIFACT_DIR,
    "forestfire_feature_reference.json"
)

feature_reference = {
    "features": feature_cols,
    "classes": label_encoder.classes_.tolist(),
    "model_type": "XGBClassifier",
    "target": "severity_tier",
    "imputer_strategy": "median"
}

with open(
    FEATURE_REF_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        feature_reference,
        f,
        indent=4
    )


# ============================================================
# VERIFY ARTIFACTS
# ============================================================

print("\n" + "=" * 60)
print("VERIFYING SAVED ARTIFACTS")
print("=" * 60)

artifact_paths = [
    MODEL_PATH,
    IMPUTER_PATH,
    LABEL_ENCODER_PATH,
    FEATURE_REF_PATH
]

for path in artifact_paths:

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"Artifact was not created:\n{path}"
        )

    file_size = os.path.getsize(path)

    print(
        f"\n{os.path.basename(path)}"
    )

    print(
        f"Size: {file_size:,} bytes"
    )

    if file_size == 0:

        raise RuntimeError(
            f"ERROR: Artifact is EMPTY:\n{path}"
        )


# ============================================================
# PRINT FEATURE INFORMATION
# ============================================================

print("\nFeatures:")

for feature in feature_cols:

    print(
        f"  - {feature}"
    )


print("\nClasses:")

print(
    label_encoder.classes_
)


print("\n" + "=" * 60)
print("✅ FOREST FIRE PRODUCTION ARTIFACTS READY!")
print("=" * 60)