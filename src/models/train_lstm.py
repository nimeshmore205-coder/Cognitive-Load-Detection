import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping

import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)



# =====================================================
# Load dataset
# =====================================================
CSV_PATH = "data/processed/features.csv"
df = pd.read_csv(CSV_PATH)


# =====================================================
# Rule-based labels (ground truth)
# =====================================================
def rule_label(row):
    ear_dev = max(0, (row["baseline_ear"] - row["avg_ear"]) / row["baseline_ear"])
    blink_dev = max(0, (row["baseline_blink_rate"] - row["blink_rate"]) / row["baseline_blink_rate"])
    score = (0.6 * ear_dev + 0.4 * blink_dev) * 100

    if score < 35:
        return "Low"
    elif score < 65:
        return "Medium"
    else:
        return "High"


df["label"] = df.apply(rule_label, axis=1)

print("\nClass distribution:")
print(df["label"].value_counts())


# =====================================================
# Feature selection
# =====================================================
features = [
    "avg_ear",
    "blink_rate",
    "ear_deviation",
    "blink_rate_deviation"
]

X = df[features].values
y = df["label"].values


# =====================================================
# Scale features
# =====================================================
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)


# =====================================================
# Encode labels
# =====================================================
le = LabelEncoder()
y_encoded = le.fit_transform(y)
num_classes = len(le.classes_)

print("\nDetected classes:", le.classes_)

y_cat = to_categorical(y_encoded, num_classes=num_classes)


# =====================================================
# Create time-series sequences
# =====================================================
SEQ_LEN = 30  # ~30 seconds window


def create_sequences(X, y, seq_len):
    Xs, ys = [], []
    for i in range(len(X) - seq_len):
        Xs.append(X[i:i + seq_len])
        ys.append(y[i + seq_len])
    return np.array(Xs), np.array(ys)


X_seq, y_seq = create_sequences(X_scaled, y_cat, SEQ_LEN)

print(f"\nCreated sequences: {X_seq.shape}")


# =====================================================
# Train / test split (temporal)
# =====================================================
split = int(0.8 * len(X_seq))

X_train, X_test = X_seq[:split], X_seq[split:]
y_train, y_test = y_seq[:split], y_seq[split:]


# =====================================================
# Build LSTM model (clean, warning-free)
# =====================================================
model = Sequential([
    Input(shape=(SEQ_LEN, X_seq.shape[2])),
    LSTM(64, return_sequences=True),
    Dropout(0.3),
    LSTM(32),
    Dropout(0.3),
    Dense(num_classes, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()


# =====================================================
# Train
# =====================================================
early_stop = EarlyStopping(
    patience=5,
    restore_best_weights=True
)

history = model.fit(
    X_train,
    y_train,
    validation_split=0.2,
    epochs=30,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)


# =====================================================
# Evaluate
# =====================================================
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nLSTM Test Accuracy: {acc:.3f}")


# =====================================================
# Save model & preprocessors
# =====================================================
model.save(os.path.join(MODEL_DIR, "lstm_cognitive_load.h5"))
joblib.dump(scaler, os.path.join(MODEL_DIR, "lstm_scaler.pkl"))
joblib.dump(le, os.path.join(MODEL_DIR, "lstm_label_encoder.pkl"))

print("\nLSTM model and preprocessors saved successfully.")
