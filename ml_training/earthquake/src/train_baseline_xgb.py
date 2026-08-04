import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import random

np.random.seed(42)
random.seed(42)

data = pd.read_csv('../data/processed/preprocessed_earthquake_data.csv')
data['time'] = pd.to_datetime(data['time'], errors='coerce', utc=True)
data = data.dropna(subset=['time']).sort_values('time').reset_index(drop=True)

data['time_diff'] = data['time'].diff().dt.total_seconds() / 3600
data['time_diff'] = data['time_diff'].fillna(0)

features_raw = ['latitude', 'longitude', 'depth', 'time_diff']
target_col = 'significant'

n = len(data)
train_end = int(n * 0.70)
val_end = int(n * 0.85)   # val fold unused by XGB itself, kept only so split boundaries match the other two scripts

train_df = data.iloc[:train_end].reset_index(drop=True)
test_df  = data.iloc[val_end:].reset_index(drop=True)   # same test rows as the LSTM/CNN-LSTM scripts

print("Class distribution (train):\n", train_df[target_col].value_counts(normalize=True))

mean_lat, mean_lon = train_df['latitude'].mean(), train_df['longitude'].mean()
for df in (train_df, test_df):
    df['dist_to_center'] = np.sqrt((df['latitude'] - mean_lat)**2 + (df['longitude'] - mean_lon)**2)

features = features_raw + ['dist_to_center']

scaler = MinMaxScaler()
train_df[features] = scaler.fit_transform(train_df[features])
test_df[features]  = scaler.transform(test_df[features])

sequence_length = 20
flat_columns = [f"{feat}_t-{sequence_length - j}" for j in range(sequence_length) for feat in features]

def make_flat_sequences(df):
    X, y = [], []
    for i in range(len(df) - sequence_length):
        X.append(df[features].iloc[i:i+sequence_length].values.flatten())
        y.append(df[target_col].iloc[i+sequence_length])
    return pd.DataFrame(X, columns=flat_columns), np.array(y)

X_train, y_train = make_flat_sequences(train_df)
X_test, y_test   = make_flat_sequences(test_df)
print(f"Train samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")

smote = SMOTE(random_state=42, sampling_strategy=1.0)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

model = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss',
    random_state=42,
)
model.fit(X_train_sm, y_train_sm)

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"\n[Baseline XGBoost] Test Accuracy: {accuracy:.4f}")
print(f"[Baseline XGBoost] Test Precision: {precision:.4f}")
print(f"[Baseline XGBoost] Test Recall: {recall:.4f}")
print(f"[Baseline XGBoost] Test F1-Score: {f1:.4f}")

cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
plt.title('Confusion Matrix — Baseline XGBoost (flattened, no sequence)')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.savefig('../results/figures/confusion_matrix_baseline_xgb.png')
plt.close()

importances = pd.Series(model.feature_importances_, index=flat_columns).sort_values(ascending=False)
print("\nTop 10 most important features:")
print(importances.head(10))

plt.figure(figsize=(8, 6))
importances.head(15).plot(kind='barh')
plt.title('Top 15 Feature Importances — Baseline XGBoost')
plt.xlabel('Importance')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('../results/figures/feature_importance_baseline_xgb.png')
plt.close()

model.save_model('../models/earthquake_baseline_xgb.json')

with open('../results/reports/baseline_xgb_results.txt', 'w') as f:
    f.write(
        f"Accuracy: {accuracy:.4f}\n"
        f"Precision: {precision:.4f}\n"
        f"Recall: {recall:.4f}\n"
        f"F1-Score: {f1:.4f}\n"
    )

np.savez(
    '../predictions/baseline_xgb_predictions.npz',
    y_test=y_test,
    y_pred_proba=y_pred_proba
)
print("\nSaved:")
print("  ../models/earthquake_baseline_xgb.json")
print("  ../results/reports/baseline_xgb_results.txt")
print("  ../predictions/baseline_xgb_predictions.npz")