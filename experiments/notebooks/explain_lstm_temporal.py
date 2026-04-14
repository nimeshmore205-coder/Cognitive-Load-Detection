import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/features.csv")

plt.figure(figsize=(12, 4))
plt.plot(df["avg_ear"], label="EAR", alpha=0.6)
plt.plot(df["blink_rate"], label="Blink Rate", alpha=0.6)

plt.title("Temporal Signals Influencing LSTM Prediction")
plt.xlabel("Time")
plt.ylabel("Value")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
