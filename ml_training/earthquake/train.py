import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from imblearn.over_sampling import SMOTE
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2
import matplotlib.pyplot as plt
import seaborn as sns
import random

np.random.seed(42)
random.seed(42)

# 1. Load your preprocessed dataset (already has 'significant' target, real magnitude, etc.)
data = pd.read_csv('preprocessed_earthquake_data.csv')
data['time'] = pd.to_datetime(data['time'], errors='coerce', utc=True)
data = data.dropna(subset=['time']).sort_values('time').reset_index(drop=True)

# 2. Feature engineering — precursor signals
data['time_diff'] = data['time'].diff().dt.total_seconds() / 3600
data['time_diff'] = data['time_diff'].fillna(0)
mean_lat, mean_lon = data['latitude'].mean(), data['longitude'].mean()
data['dist_to_center'] = np.sqrt((data['latitude'] - mean_lat)**2 + (data['longitude'] - mean_lon)**2)

features = ['latitude', 'longitude', 'depth', 'time_diff', 'dist_to_center']
target = data['significant']  # M >= 5.5, already computed in preprocessing

print("Class distribution:\n", target.value_counts(normalize=True))

scaler = MinMaxScaler()
data[features] = scaler.fit_transform(data[features])

# 3. Create sequences for LSTM
sequence_length = 20
X, y = [], []
for i in range(len(data) - sequence_length):
    X.append(data[features].iloc[i:i+sequence_length].values)
    y.append(target.iloc[i+sequence_length])

X = np.array(X)
y = np.array(y)
print(f"Sequences created: {X.shape[0]}")

# 4. Apply SMOTE to balance classes
X_reshaped = X.reshape(X.shape[0], -1)
smote = SMOTE(random_state=42, sampling_strategy=1.0)
X_smote, y_smote = smote.fit_resample(X_reshaped, y)
X_smote = X_smote.reshape(-1, sequence_length, len(features))

# 5. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_smote, y_smote, test_size=0.2, random_state=42, stratify=y_smote
)

# 6. Class weights (extra safety alongside SMOTE)
classes = np.unique(y_train)
class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight_dict = dict(zip(classes, class_weights))

# 7. Build CNN-LSTM model
model = Sequential([
    Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(sequence_length, len(features))),
    MaxPooling1D(pool_size=2),
    BatchNormalization(),
    LSTM(20, return_sequences=False),
    Dense(8, activation='relu', kernel_regularizer=l2(0.01)),
    Dropout(0.4),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer=Adam(learning_rate=0.0001), loss='binary_crossentropy',
              metrics=['accuracy', 'Precision', 'Recall'])
model.summary()

# 8. Train
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

# 9. Evaluate
loss, accuracy, precision, recall = model.evaluate(X_test, y_test)
f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
print(f"\nTest Accuracy: {accuracy:.4f}")
print(f"Test Precision: {precision:.4f}")
print(f"Test Recall: {recall:.4f}")
print(f"Test F1-Score: {f1:.4f}")

# 10. Confusion matrix
y_pred = model.predict(X_test)
y_pred_binary = (y_pred > 0.5).astype(int)
cm = confusion_matrix(y_test, y_pred_binary)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.savefig('confusion_matrix.png')

# 11. Save the trained model — this is what your FastAPI app will load later
model.save('earthquake_cnn_lstm.keras')
print("\nModel saved as 'earthquake_cnn_lstm.keras'")

# 12. Save the scaler too — needed to preprocess live data the same way at inference time
import joblib
joblib.dump(scaler, 'earthquake_scaler.pkl')
print("Scaler saved as 'earthquake_scaler.pkl'")