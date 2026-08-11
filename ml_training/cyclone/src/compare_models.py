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


# ============================================================
# Prediction files
# ============================================================

MODEL_FILES = {
    "CNN-LSTM": "cyclone/predictions/cnn_lstm_predictions.npz",
    "Baseline LSTM": "cyclone/predictions/baseline_lstm_predictions.npz",
    "Baseline XGB": "cyclone/predictions/baseline_xgb_predictions.npz",
}

MAIN_MODEL = "CNN-LSTM"


# ============================================================
# Calculate metrics
# ============================================================

def compute_metrics(y_true, y_prob, threshold=0.5):

    y_pred = (y_prob >= threshold).astype(int)

    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(
            y_true, y_pred, zero_division=0
        ),
        "Recall": recall_score(
            y_true, y_pred, zero_division=0
        ),
        "F1": f1_score(
            y_true, y_pred, zero_division=0
        ),
        "ROC-AUC": roc_auc_score(
            y_true, y_prob
        ),
        "PR-AUC": average_precision_score(
            y_true, y_prob
        ),
    }

    return metrics, y_pred


# ============================================================
# Main
# ============================================================

def main():

    print("Loading model prediction files...")

    results = {}
    predictions = {}
    truths = {}

    # --------------------------------------------------------
    # Load all prediction files
    # --------------------------------------------------------

    for model_name, file_path in MODEL_FILES.items():

        print(f"\nLoading: {model_name}")
        print(f"File: {file_path}")

        data = np.load(file_path)

        y_true = data["y_test"]
        y_prob = data["y_pred_proba"]

        print(f"Test samples: {len(y_true)}")

        metrics, y_pred = compute_metrics(
            y_true,
            y_prob
        )

        results[model_name] = metrics
        predictions[model_name] = y_pred
        truths[model_name] = y_true

    # --------------------------------------------------------
    # Summary table
    # --------------------------------------------------------

    results_df = pd.DataFrame(results).T

    results_df = results_df.round(4)

    print("\n")
    print("=" * 70)
    print("CYCLONE MODEL COMPARISON")
    print("=" * 70)

    print(results_df.to_string())

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    results_df.to_csv(
        "cyclone/results/model_comparison_summary.csv"
    )

    print("\nSaved:")
    print(
        "cyclone/results/model_comparison_summary.csv"
    )

    # --------------------------------------------------------
    # Comparison chart
    # --------------------------------------------------------

    ax = results_df.plot(
        kind="bar",
        figsize=(12, 7),
        rot=0
    )

    ax.set_title(
        "Cyclone Intensification Model Comparison"
    )

    ax.set_ylabel("Score")

    ax.set_ylim(0, 1.05)

    ax.legend(
        loc="lower right",
        ncol=3
    )

    plt.tight_layout()

    plt.savefig(
        "cyclone/results/model_comparison_chart.png",
        dpi=150
    )

    plt.close()

    print(
        "cyclone/results/model_comparison_chart.png"
    )

    # --------------------------------------------------------
    # Find best model for each metric
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("BEST MODEL BY METRIC")
    print("=" * 70)

    for metric in results_df.columns:

        best_model = results_df[metric].idxmax()
        best_score = results_df.loc[
            best_model, metric
        ]

        print(
            f"{metric:12s}: "
            f"{best_model:15s} = {best_score:.4f}"
        )

    # --------------------------------------------------------
    # McNemar's statistical test
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print(f"McNemar's Test vs {MAIN_MODEL}")
    print("=" * 70)

    y_true_main = truths[MAIN_MODEL]

    main_correct = (
        predictions[MAIN_MODEL] == y_true_main
    )

    for model_name in MODEL_FILES:

        if model_name == MAIN_MODEL:
            continue

        # Make sure both models used the same test labels
        if not np.array_equal(
            y_true_main,
            truths[model_name]
        ):

            print(
                f"{MAIN_MODEL} vs {model_name}: "
                "SKIPPED - different test sets"
            )

            continue

        other_correct = (
            predictions[model_name] == y_true_main
        )

        both_correct = np.sum(
            main_correct & other_correct
        )

        main_only = np.sum(
            main_correct & ~other_correct
        )

        other_only = np.sum(
            ~main_correct & other_correct
        )

        neither = np.sum(
            ~main_correct & ~other_correct
        )

        table = [
            [both_correct, main_only],
            [other_only, neither]
        ]

        result = mcnemar(
            table,
            exact=False,
            correction=True
        )

        if result.pvalue < 0.05:
            significance = "significant"
        else:
            significance = "not significant"

        print(
            f"{MAIN_MODEL} vs {model_name}: "
            f"statistic={result.statistic:.3f}, "
            f"p-value={result.pvalue:.4f} "
            f"-> {significance}"
        )

    # --------------------------------------------------------
    # Final conclusion
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("FINAL CONCLUSION")
    print("=" * 70)

    best_f1_model = results_df["F1"].idxmax()
    best_f1_score = results_df.loc[
        best_f1_model, "F1"
    ]

    best_accuracy_model = results_df[
        "Accuracy"
    ].idxmax()

    print(
        f"Best F1 model      : "
        f"{best_f1_model} ({best_f1_score:.4f})"
    )

    print(
        f"Best Accuracy model: "
        f"{best_accuracy_model} "
        f"({results_df.loc[best_accuracy_model, 'Accuracy']:.4f})"
    )

    print("\nComparison completed successfully.")


if __name__ == "__main__":
    main()