"""
compare_models.py
------------------
Standalone comparison script. Does NOT train anything.
Loads each model's saved predictions and produces:

- Summary table (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC)
- Grouped comparison chart
- McNemar's statistical test between CNN-LSTM and each baseline

Requires each training script to save prediction files in:

../predictions/
    cnn_lstm_predictions.npz
    baseline_lstm_predictions.npz
    baseline_xgb_predictions.npz
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score
)
from statsmodels.stats.contingency_tables import mcnemar

# Prediction files
MODEL_FILES = {
    "CNN-LSTM": "../predictions/cnn_lstm_predictions.npz",
    "Baseline LSTM": "../predictions/baseline_lstm_predictions.npz",
    "Baseline XGB": "../predictions/baseline_xgb_predictions.npz",
}

# Main model for statistical comparison
MAIN_MODEL = "CNN-LSTM"


def compute_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob > threshold).astype(int)

    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, y_prob),
        "PR-AUC": average_precision_score(y_true, y_prob),
    }

    return metrics, y_pred


def main():

    results = {}
    preds = {}
    truths = {}

    # ===============================
    # Load prediction files
    # ===============================
    for name, path in MODEL_FILES.items():
        data = np.load(path)

        y_true = data["y_test"]
        y_prob = data["y_pred_proba"]

        metrics, y_pred = compute_metrics(y_true, y_prob)

        results[name] = metrics
        preds[name] = y_pred
        truths[name] = y_true

    # ===============================
    # Summary Table
    # ===============================
    df = pd.DataFrame(results).T
    df = df.round(4)

    print("\n=== Model Comparison ===")
    print(df.to_string())

    df.to_csv(
        "../results/csv/model_comparison_summary.csv",
        index=True
    )

    # ===============================
    # Comparison Chart
    # ===============================
    ax = df.plot(
        kind="bar",
        figsize=(10, 6),
        rot=0
    )

    ax.set_title("Model Comparison — Earthquake Significance Prediction")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right", ncol=3)

    plt.tight_layout()

    plt.savefig(
        "../results/figures/model_comparison_chart.png",
        dpi=150
    )

    plt.close()

    print("\nSaved:")
    print("  ../results/csv/model_comparison_summary.csv")
    print("  ../results/figures/model_comparison_chart.png")

    # ===============================
    # McNemar's Test
    # ===============================
    print(f"\n=== McNemar's test vs {MAIN_MODEL} ===")

    y_true_ref = truths[MAIN_MODEL]
    main_correct = preds[MAIN_MODEL] == y_true_ref

    for name in MODEL_FILES:

        if name == MAIN_MODEL:
            continue

        if not np.array_equal(y_true_ref, truths[name]):
            print(
                f"{name}: SKIPPED — y_test differs from {MAIN_MODEL}'s test set."
            )
            continue

        other_correct = preds[name] == y_true_ref

        both_correct = np.sum(main_correct & other_correct)
        main_only = np.sum(main_correct & ~other_correct)
        other_only = np.sum(~main_correct & other_correct)
        neither = np.sum(~main_correct & ~other_correct)

        table = [
            [both_correct, main_only],
            [other_only, neither]
        ]

        result = mcnemar(
            table,
            exact=False,
            correction=True
        )

        significance = (
            "significant (p < 0.05)"
            if result.pvalue < 0.05
            else "not significant"
        )

        print(
            f"{MAIN_MODEL} vs {name}: "
            f"statistic={result.statistic:.3f}, "
            f"p-value={result.pvalue:.4f} -> {significance}"
        )


if __name__ == "__main__":
    main()