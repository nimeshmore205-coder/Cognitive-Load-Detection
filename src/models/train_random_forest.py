import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib

# -----------------------------
# Load dataset
# -----------------------------
CSV_PATH = "data/processed/features.csv"
df = pd.read_csv(CSV_PATH)

# -----------------------------
# Recompute cognitive load score (same logic)
# -----------------------------
def compute_load(row):
    ear_dev = max(0, (row["baseline_ear"] - row["avg_ear"]) / row["baseline_ear"])
    blink_dev = max(0, (row["baseline_blink_rate"] - row["blink_rate"]) / row["baseline_blink_rate"])
    score = (0.6 * ear_dev + 0.4 * blink_dev) * 100

    if score < 35:
        return "Low"
    elif score < 65:
        return "Medium"
    else:
        return "High"

df["load_label"] = df.apply(compute_load, axis=1)

# -----------------------------
# Feature selection
# -----------------------------
features = [
    "avg_ear",
    "blink_rate",
    "ear_deviation",
    "blink_rate_deviation"
]

X = df[features]
y = df["load_label"]

# -----------------------------
# Encode labels
# -----------------------------
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# -----------------------------
# Train / test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.25, random_state=42, stratify=y_encoded
)

# -----------------------------
# Train Random Forest
# -----------------------------
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42,
    class_weight="balanced"
)

rf.fit(X_train, y_train)

# -----------------------------
# Evaluate
# -----------------------------
y_pred = rf.predict(X_test)

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, target_names=le.classes_))

print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# -----------------------------
# Feature importance
# -----------------------------
print("\nFeature Importances:")
for name, imp in zip(features, rf.feature_importances_):
    print(f"{name}: {imp:.3f}")

# -----------------------------
# Save model
# -----------------------------
MODEL_PATH = "models/random_forest_cognitive_load.pkl"
joblib.dump((rf, le), MODEL_PATH)

print(f"\nModel saved to {MODEL_PATH}")
