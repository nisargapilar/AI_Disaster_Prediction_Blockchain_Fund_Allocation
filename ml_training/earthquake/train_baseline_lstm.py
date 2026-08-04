import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
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
    X.append(data[features].iloc[i:i+sequence_length].values)
    y.append(target.iloc[i+sequence_length])

X = np.array(X)
y = np.array(y)
print(f"Sequences created: {X.shape[0]}")

X_reshaped = X.reshape(X.shape[0], -1)
smote = SMOTE(random_state=42, sampling_strategy=1.0)
X_smote, y_smote = smote.fit_resample(X_reshaped, y)
X_smote = X_smote.reshape(-1, sequence_length, len(features))

X_train, X_test, y_train, y_test = train_test_split(
    X_smote, y_smote, test_size=0.2, random_state=42, stratify=y_smote
)

classes = np.unique(y_train)
class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight_dict = dict(zip(classes, class_weights))

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
    X_train, y_train,
    epochs=15,
    batch_size=32,
    validation_data=(X_test, y_test),
    class_weight=class_weight_dict,
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
plt.savefig('confusion_matrix_baseline_lstm.png')

model.save('earthquake_baseline_lstm.keras')
print("\nModel saved as 'earthquake_baseline_lstm.keras'")

with open('baseline_lstm_results.txt', 'w') as f:
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Precision: {precision:.4f}\n")
    f.write(f"Recall: {recall:.4f}\n")
    f.write(f"F1-Score: {f1:.4f}\n")
print("Results saved to 'baseline_lstm_results.txt'")