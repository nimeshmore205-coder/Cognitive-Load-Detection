import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Load dataset
# ==============================
CSV_PATH = "data/processed/features.csv"
df = pd.read_csv(CSV_PATH)

# ==============================
# Create fatigue score (same logic as rule-based)
# ==============================
def fatigue_score(row):
    ear_dev = max(0, (row["baseline_ear"] - row["avg_ear"]) / row["baseline_ear"])
    blink_dev = max(0, (row["baseline_blink_rate"] - row["blink_rate"]) / row["baseline_blink_rate"])
    return (0.6 * ear_dev + 0.4 * blink_dev) * 100

df["fatigue_score"] = df.apply(fatigue_score, axis=1)

# ==============================
# Rolling average (trend)
# ==============================
WINDOW = 30   # ~30 seconds
df["fatigue_trend"] = df["fatigue_score"].rolling(WINDOW).mean()

# ==============================
# Plot
# ==============================
plt.figure(figsize=(12, 5))

plt.plot(df["fatigue_score"], alpha=0.4, label="Instantaneous Load")
plt.plot(df["fatigue_trend"], linewidth=3, label="Fatigue Trend (Rolling Avg)")

plt.axhline(35, linestyle="--", color="green", label="Low Threshold")
plt.axhline(65, linestyle="--", color="red", label="High Threshold")

plt.title("Cognitive Load & Fatigue Trend Over Time")
plt.xlabel("Time (samples)")
plt.ylabel("Cognitive Load Score")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
