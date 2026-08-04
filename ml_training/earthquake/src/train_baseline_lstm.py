import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import confusion_matrix
from imblearn.over_sampling import SMOTE
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2
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
val_end = int(n * 0.85)

train_df = data.iloc[:train_end].reset_index(drop=True)
val_df   = data.iloc[train_end:val_end].reset_index(drop=True)
test_df  = data.iloc[val_end:].reset_index(drop=True)

print("Class distribution (train):\n", train_df[target_col].value_counts(normalize=True))

mean_lat, mean_lon = train_df['latitude'].mean(), train_df['longitude'].mean()
for df in (train_df, val_df, test_df):
    df['dist_to_center'] = np.sqrt((df['latitude'] - mean_lat)**2 + (df['longitude'] - mean_lon)**2)

features = features_raw + ['dist_to_center']

scaler = MinMaxScaler()
train_df[features] = scaler.fit_transform(train_df[features])
val_df[features]   = scaler.transform(val_df[features])
test_df[features]  = scaler.transform(test_df[features])

sequence_length = 20

def make_sequences(df):
    X, y = [], []
    for i in range(len(df) - sequence_length):
        X.append(df[features].iloc[i:i+sequence_length].values)
        y.append(df[target_col].iloc[i+sequence_length])
    return np.array(X), np.array(y)

X_train, y_train = make_sequences(train_df)
X_val, y_val     = make_sequences(val_df)
X_test, y_test   = make_sequences(test_df)
print(f"Train seq: {X_train.shape[0]}, Val seq: {X_val.shape[0]}, Test seq: {X_test.shape[0]}")

X_train_flat = X_train.reshape(X_train.shape[0], -1)
smote = SMOTE(random_state=42, sampling_strategy=1.0)
X_train_sm, y_train_sm = smote.fit_resample(X_train_flat, y_train)
X_train_sm = X_train_sm.reshape(-1, sequence_length, len(features))

# Plain LSTM — no Conv1D / MaxPooling / BatchNormalization
model = Sequential([
    LSTM(20, return_sequences=False, input_shape=(sequence_length, len(features))),
    Dense(8, activation='relu', kernel_regularizer=l2(0.01)),
    Dropout(0.4),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer=Adam(learning_rate=0.0001), loss='binary_crossentropy',
              metrics=['accuracy', 'Precision', 'Recall'])
model.summary()

early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
history = model.fit(
    X_train_sm, y_train_sm,
    epochs=15,
    batch_size=32,
    validation_data=(X_val, y_val),
    callbacks=[early_stopping],
    verbose=1
)

loss, accuracy, precision, recall = model.evaluate(X_test, y_test)
f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
print(f"\n[Baseline LSTM] Test Accuracy: {accuracy:.4f}")
print(f"[Baseline LSTM] Test Precision: {precision:.4f}")
print(f"[Baseline LSTM] Test Recall: {recall:.4f}")
print(f"[Baseline LSTM] Test F1-Score: {f1:.4f}")

y_pred = model.predict(X_test)
y_pred_binary = (y_pred > 0.5).astype(int)
cm = confusion_matrix(y_test, y_pred_binary)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
plt.title('Confusion Matrix — Baseline LSTM (no CNN front-end)')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.savefig('../results/figures/confusion_matrix_baseline_lstm.png')
model.save('../models/earthquake_baseline_lstm.keras')

with open('../results/reports/baseline_lstm_results.txt', 'w') as f:
     f.write(f"Accuracy: {accuracy:.4f}\nPrecision: {precision:.4f}\nRecall: {recall:.4f}\nF1-Score: {f1:.4f}\n")

np.savez(
    '../predictions/baseline_lstm_predictions.npz',
    y_test=y_test,
    y_pred_proba=y_pred.ravel()
)
print("\nSaved:")
print("  ../models/earthquake_baseline_lstm.keras")
print("  ../results/reports/baseline_lstm_results.txt")
print("  ../predictions/baseline_lstm_predictions.npz")