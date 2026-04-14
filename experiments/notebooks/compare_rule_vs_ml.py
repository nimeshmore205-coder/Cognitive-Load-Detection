import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix

# -----------------------------
# Load dataset
# -----------------------------
CSV_PATH = "data/processed/features.csv"
df = pd.read_csv(CSV_PATH)

# -----------------------------
# Rule-based labeling
# -----------------------------
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

df["rule_label"] = df.apply(rule_label, axis=1)

# -----------------------------
# Load ML model
# -----------------------------
model, label_encoder = joblib.load("models/random_forest_cognitive_load.pkl")

X = df[["avg_ear", "blink_rate", "ear_deviation", "blink_rate_deviation"]]
ml_preds = model.predict(X)
df["ml_label"] = label_encoder.inverse_transform(ml_preds)

# -----------------------------
# Accuracy comparison
# -----------------------------
rule_acc = accuracy_score(df["rule_label"], df["rule_label"])  # self-reference
ml_acc = accuracy_score(df["rule_label"], df["ml_label"])

print(f"Rule-based Accuracy (baseline): {rule_acc:.3f}")
print(f"ML-based Accuracy: {ml_acc:.3f}")

# -----------------------------
# Confusion matrix
# -----------------------------
cm = confusion_matrix(df["rule_label"], df["ml_label"], labels=["Low", "Medium", "High"])

plt.figure(figsize=(5, 4))
plt.imshow(cm)
plt.title("Rule vs ML Confusion Matrix")
plt.xticks(range(3), ["Low", "Medium", "High"])
plt.yticks(range(3), ["Low", "Medium", "High"])
plt.colorbar()

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, cm[i, j], ha="center", va="center")

plt.xlabel("ML Prediction")
plt.ylabel("Rule Label")
plt.tight_layout()
plt.show()

# -----------------------------
# Agreement over time
# -----------------------------
agreement = df["rule_label"] == df["ml_label"]

plt.figure(figsize=(12, 4))
plt.plot(agreement.astype(int))
plt.title("Rule vs ML Agreement Over Time")
plt.ylabel("Agreement (1 = Same, 0 = Different)")
plt.xlabel("Sample Index")
plt.grid(True)
plt.tight_layout()
plt.show()
