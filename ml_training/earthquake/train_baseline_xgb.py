import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import random

np.random.seed(42)
random.seed(42)

data = pd.read_csv('preprocessed_earthquake_data.csv')
data['time'] = pd.to_datetime(data['time'], errors='coerce', utc=True)
data = data.dropna(subset=['time']).sort_values('time').reset_index(drop=True)

data['time_diff'] = data['time'].diff().dt.total_seconds() / 3600
data['time_diff'] = data['time_diff'].fillna(0)
mean_lat, mean_lon = data['latitude'].mean(), data['longitude'].mean()
data['dist_to_center'] = np.sqrt((data['latitude'] - mean_lat)**2 + (data['longitude'] - mean_lon)**2)

features = ['latitude', 'longitude', 'depth', 'time_diff', 'dist_to_center']
target = data['significant']

print("Class distribution:\n", target.value_counts(normalize=True))

scaler = MinMaxScaler()
data[features] = scaler.fit_transform(data[features])

sequence_length = 20
X, y = [], []
for i in range(len(data) - sequence_length):
    window = data[features].iloc[i:i+sequence_length].values.flatten()
    X.append(window)
    y.append(target.iloc[i+sequence_length])

X = np.array(X)
y = np.array(y)

flat_columns = [f"{feat}_t-{sequence_length - j}" for j in range(sequence_length) for feat in features]
X_df = pd.DataFrame(X, columns=flat_columns)
print(f"Flattened samples created: {X_df.shape[0]}, features per sample: {X_df.shape[1]}")

smote = SMOTE(random_state=42, sampling_strategy=1.0)
X_smote, y_smote = smote.fit_resample(X_df, y)

X_train, X_test, y_train, y_test = train_test_split(
    X_smote, y_smote, test_size=0.2, random_state=42, stratify=y_smote
)

model = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss',
    random_state=42,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
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
plt.savefig('confusion_matrix_baseline_xgb.png')

importances = pd.Series(model.feature_importances_, index=flat_columns).sort_values(ascending=False)
print("\nTop 10 most important features:")
print(importances.head(10))

plt.figure(figsize=(8, 6))
importances.head(15).plot(kind='barh')
plt.title('Top 15 Feature Importances — Baseline XGBoost')
plt.xlabel('Importance')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('feature_importance_baseline_xgb.png')

model.save_model('earthquake_baseline_xgb.json')
print("\nModel saved as 'earthquake_baseline_xgb.json'")

with open('baseline_xgb_results.txt', 'w') as f:
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Precision: {precision:.4f}\n")
    f.write(f"Recall: {recall:.4f}\n")
    f.write(f"F1-Score: {f1:.4f}\n")
print("Results saved to 'baseline_xgb_results.txt'")