import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Load dataset
# -----------------------------
CSV_PATH = "data/processed/features.csv"
df = pd.read_csv(CSV_PATH)

# -----------------------------
# Convert timestamp
# -----------------------------
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

# -----------------------------
# Compute Cognitive Load Score (same logic as runtime)
# -----------------------------
def compute_load(row):
    ear_dev = max(0, (row["baseline_ear"] - row["avg_ear"]) / row["baseline_ear"])
    blink_dev = max(0, (row["baseline_blink_rate"] - row["blink_rate"]) / row["baseline_blink_rate"])
    return (0.6 * ear_dev + 0.4 * blink_dev) * 100

df["cognitive_load"] = df.apply(compute_load, axis=1)

# -----------------------------
# Smooth for visualization
# -----------------------------
df["load_smooth"] = df["cognitive_load"].rolling(window=30).mean()

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(12, 6))
plt.plot(df["timestamp"], df["load_smooth"])
plt.xlabel("Time")
plt.ylabel("Cognitive Load Score")
plt.title("Cognitive Load / Fatigue Trend Over Time")
plt.grid(True)
plt.tight_layout()
plt.show()
