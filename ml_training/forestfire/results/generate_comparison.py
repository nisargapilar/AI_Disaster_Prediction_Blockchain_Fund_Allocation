import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CSV_DIR = os.path.join(RESULTS_DIR, "csv")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)


# ============================================================
# LOAD DATASET
# ============================================================

archive_path = os.path.join(
    DATA_DIR,
    "fire_archive_M6_107977.csv"
)

nrt_path = os.path.join(
    DATA_DIR,
    "fire_nrt_M6_107977.csv"
)

print("Loading datasets...")

df_archive = pd.read_csv(archive_path)
df_nrt = pd.read_csv(nrt_path)

df = pd.concat(
    [df_archive, df_nrt],
    ignore_index=True
)

print(f"Total records: {len(df)}")


# ============================================================
# CREATE SEVERITY TIERS
# ============================================================

quantiles = df["frp"].quantile(
    [1/3, 2/3]
).values

low_medium_threshold = quantiles[0]
medium_high_threshold = quantiles[1]

print("\nFRP thresholds:")
print(
    f"Low/Medium : {low_medium_threshold:.4f}"
)
print(
    f"Medium/High: {medium_high_threshold:.4f}"
)


def frp_to_tier(frp):

    if frp <= low_medium_threshold:
        return "low"

    elif frp <= medium_high_threshold:
        return "medium"

    else:
        return "high"


df["severity_tier"] = df["frp"].apply(
    frp_to_tier
)


print("\nSeverity distribution:")
print(
    df["severity_tier"].value_counts()
)


# ============================================================
# FEATURE ENGINEERING
# ============================================================

df["daynight_encoded"] = (
    df["daynight"].map({
        "D": 1,
        "N": 0
    })
)

df["acq_date"] = pd.to_datetime(
    df["acq_date"]
)

df["month"] = df["acq_date"].dt.month

df["day_of_year"] = (
    df["acq_date"].dt.dayofyear
)


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
# HANDLE MISSING VALUES
# ============================================================

print("\nMissing values:")
print(X.isnull().sum())

imputer = SimpleImputer(
    strategy="median"
)

X = pd.DataFrame(
    imputer.fit_transform(X),
    columns=feature_cols
)

print(
    "\nRemaining missing values:",
    X.isnull().sum().sum()
)


# ============================================================
# ENCODE TARGET
# ============================================================

label_encoder = LabelEncoder()

y_encoded = label_encoder.fit_transform(y)

print("\nClasses:")
print(label_encoder.classes_)


# ============================================================
# TRAIN TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.20,
    random_state=42,
    stratify=y_encoded
)

print(
    f"\nTraining samples: {len(X_train)}"
)

print(
    f"Testing samples : {len(X_test)}"
)


# ============================================================
# DEFINE MODELS
# ============================================================

models = {

    "Logistic Regression": Pipeline([
        (
            "scaler",
            StandardScaler()
        ),

        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                random_state=42
            )
        )
    ]),

    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1
    ),

    "XGBoost": XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=2,
        gamma=0.1,
        reg_alpha=0.05,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=len(label_encoder.classes_),
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1
    )
}


# ============================================================
# TRAIN AND EVALUATE
# ============================================================

results = {}

trained_models = {}

for name, model in models.items():

    print("\n" + "=" * 60)

    print(
        f"Training {name}..."
    )

    model.fit(
        X_train,
        y_train
    )

    y_pred = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        average="macro"
    )

    recall = recall_score(
        y_test,
        y_pred,
        average="macro"
    )

    f1 = f1_score(
        y_test,
        y_pred,
        average="macro"
    )

    results[name] = {
        "Accuracy": accuracy * 100,
        "Precision": precision * 100,
        "Recall": recall * 100,
        "F1-Score": f1 * 100
    }

    trained_models[name] = model

    print(
        f"Accuracy : {accuracy:.4%}"
    )

    print(
        f"Precision: {precision:.4%}"
    )

    print(
        f"Recall   : {recall:.4%}"
    )

    print(
        f"F1-Score : {f1:.4%}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            y_pred,
            target_names=label_encoder.classes_
        )
    )

    # --------------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------------

    cm = confusion_matrix(
        y_test,
        y_pred
    )

    plt.figure(
        figsize=(7, 6)
    )

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=label_encoder.classes_
    )

    disp.plot(
        ax=plt.gca()
    )

    plt.title(
        f"{name} - Confusion Matrix"
    )

    plt.tight_layout()

    filename = (
        name.lower()
        .replace(" ", "_")
        + "_confusion_matrix.png"
    )

    plt.savefig(
        os.path.join(
            FIGURES_DIR,
            filename
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# MODEL COMPARISON CSV
# ============================================================

comparison_df = pd.DataFrame(
    results
).T

comparison_df.index.name = "Model"

comparison_df = comparison_df.round(2)

comparison_path = os.path.join(
    CSV_DIR,
    "model_comparison.csv"
)

comparison_df.to_csv(
    comparison_path
)

print("\nModel Comparison:")
print(comparison_df)

print(
    f"\nSaved: {comparison_path}"
)


# ============================================================
# MODEL COMPARISON GRAPH
# ============================================================

comparison_df.plot(
    kind="bar",
    figsize=(11, 7)
)

plt.title(
    "Forest Fire Severity Model Comparison"
)

plt.ylabel(
    "Score (%)"
)

plt.xlabel(
    "Machine Learning Model"
)

plt.xticks(
    rotation=0
)

plt.legend(
    title="Metrics"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIGURES_DIR,
        "model_comparison.png"
    ),
    dpi=300
)

plt.close()


# ============================================================
# ACCURACY-ONLY GRAPH
# ============================================================

plt.figure(
    figsize=(9, 6)
)

plt.bar(
    comparison_df.index,
    comparison_df["Accuracy"]
)

plt.ylabel(
    "Accuracy (%)"
)

plt.xlabel(
    "Model"
)

plt.title(
    "Forest Fire Severity Prediction Accuracy"
)

plt.xticks(
    rotation=0
)

plt.ylim(
    0,
    100
)

for i, value in enumerate(
    comparison_df["Accuracy"]
):

    plt.text(
        i,
        value + 1,
        f"{value:.2f}%",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIGURES_DIR,
        "accuracy_comparison.png"
    ),
    dpi=300
)

plt.close()


# ============================================================
# XGBOOST FEATURE IMPORTANCE
# ============================================================

xgb_model = trained_models[
    "XGBoost"
]

importance = xgb_model.feature_importances_

feature_importance_df = pd.DataFrame({
    "Feature": feature_cols,
    "Importance": importance
})

feature_importance_df = (
    feature_importance_df
    .sort_values(
        "Importance",
        ascending=False
    )
)

print("\nXGBoost Feature Importance:")

print(
    feature_importance_df
)


feature_importance_df.to_csv(
    os.path.join(
        CSV_DIR,
        "xgboost_feature_importance.csv"
    ),
    index=False
)


plt.figure(
    figsize=(10, 7)
)

plt.barh(
    feature_importance_df["Feature"],
    feature_importance_df["Importance"]
)

plt.xlabel(
    "Importance"
)

plt.ylabel(
    "Feature"
)

plt.title(
    "XGBoost Feature Importance"
)

plt.gca().invert_yaxis()

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIGURES_DIR,
        "xgboost_feature_importance.png"
    ),
    dpi=300
)

plt.close()


# ============================================================
# SAVE FINAL XGBOOST ARTIFACTS
# ============================================================

joblib.dump(
    xgb_model,
    os.path.join(
        BASE_DIR,
        "models",
        "fire_severity_xgb_model.pkl"
    )
)

joblib.dump(
    label_encoder,
    os.path.join(
        BASE_DIR,
        "models",
        "severity_label_encoder.pkl"
    )
)

joblib.dump(
    feature_cols,
    os.path.join(
        BASE_DIR,
        "models",
        "feature_columns.pkl"
    )
)

joblib.dump(
    imputer,
    os.path.join(
        BASE_DIR,
        "models",
        "fire_severity_imputer.pkl"
    )
)


# ============================================================
# FINAL RESULT
# ============================================================

best_model = comparison_df[
    "Accuracy"
].idxmax()

best_accuracy = comparison_df.loc[
    best_model,
    "Accuracy"
]

print("\n" + "=" * 60)

print(
    f"BEST MODEL: {best_model}"
)

print(
    f"BEST ACCURACY: {best_accuracy:.2f}%"
)

print("=" * 60)

print(
    "\nModel comparison completed successfully!"
)