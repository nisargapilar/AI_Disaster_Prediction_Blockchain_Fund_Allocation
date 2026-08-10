import os
import pandas as pd


# ============================================================
# FLOOD MODEL COMPARISON
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "results"
)

os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# MODEL RESULTS
# ============================================================

results = pd.DataFrame({
    "Model": [
        "Baseline LSTM",
        "Baseline XGBoost",
        "CNN-LSTM",
        "Corrected LSTM"
    ],

    "MAE": [
        0.003740,
        0.011320,
        0.026525,
        0.002053
    ],

    "RMSE": [
        0.004122,
        0.014447,
        0.028078,
        0.002553
    ],

    "R2": [
        0.993178,
        0.916196,
        0.683458,
        0.997384
    ]
})


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\nFinal Model Comparison:")
print(results.to_string(index=False))


# ============================================================
# SAVE RESULTS
# ============================================================

output_path = os.path.join(
    RESULTS_DIR,
    "final_model_comparison.csv"
)

results.to_csv(
    output_path,
    index=False
)

print("\nFinal model comparison saved successfully!")
print(output_path)