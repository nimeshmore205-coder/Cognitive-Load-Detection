import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

from tensorflow.keras.models import load_model   # type: ignore

# ==============================
# Page config
# ==============================
st.set_page_config(
    page_title="Cognitive Load Dashboard",
    layout="wide"
)

st.title("🧠 Cognitive Load Detection Dashboard")
st.caption("Real-time cognitive monitoring using computer vision & ML")

# ==============================
# Load models
# ==============================
rf_model, rf_le = joblib.load("models/random_forest_cognitive_load.pkl")

lstm_model = load_model("models/lstm_cognitive_load.h5")
lstm_scaler = joblib.load("models/lstm_scaler.pkl")
lstm_le = joblib.load("models/lstm_label_encoder.pkl")

# ==============================
# Load dataset
# ==============================
CSV_PATH = "data/processed/features.csv"
df = pd.read_csv(CSV_PATH)

st.success("Dataset loaded successfully")

# ==============================
# Sidebar controls
# ==============================
st.sidebar.header("Controls")

sample_index = st.sidebar.slider(
    "Select Time Index",
    min_value=0,
    max_value=len(df) - 1,
    value=len(df) - 1
)

# ==============================
# Feature extraction
# ==============================
row = df.iloc[sample_index]

avg_ear = row["avg_ear"]
blink_rate = row["blink_rate"]
ear_dev = row["ear_deviation"]
blink_dev = row["blink_rate_deviation"]

# ==============================
# RF Prediction
# ==============================
rf_pred = rf_model.predict([[avg_ear, blink_rate, ear_dev, blink_dev]])[0]
rf_label = rf_le.inverse_transform([rf_pred])[0]

# ==============================
# Display metrics
# ==============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("EAR", f"{avg_ear:.3f}")
col2.metric("Blink Rate (/min)", f"{blink_rate:.1f}")
col3.metric("EAR Deviation", f"{ear_dev:.3f}")
col4.metric("Blink Deviation", f"{blink_dev:.3f}")

st.divider()

# ==============================
# Load results
# ==============================
st.subheader("🧠 Cognitive Load Prediction")

st.write(f"**Random Forest Prediction:** `{rf_label}`")

# ==============================
# Fatigue trend plot
# ==============================
st.subheader("📈 Fatigue Trend Over Time")

def fatigue_score(row):
    return (0.6 * row["ear_deviation"] + 0.4 * row["blink_rate_deviation"]) * 100

df["fatigue_score"] = df.apply(fatigue_score, axis=1)
df["fatigue_trend"] = df["fatigue_score"].rolling(30).mean()

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["fatigue_score"], alpha=0.3, label="Instant Load")
ax.plot(df["fatigue_trend"], linewidth=2, label="Fatigue Trend")

ax.axhline(35, linestyle="--", color="green", label="Low Threshold")
ax.axhline(65, linestyle="--", color="red", label="High Threshold")

ax.set_xlabel("Time")
ax.set_ylabel("Load Score")
ax.legend()
ax.grid(True)

st.pyplot(fig)

# ==============================
# Explainability
# ==============================
st.subheader("🔍 Model Explanation (Feature Importance)")

importance = rf_model.feature_importances_
features = ["avg_ear", "blink_rate", "ear_deviation", "blink_rate_deviation"]

fig2, ax2 = plt.subplots()
ax2.barh(features, importance)
ax2.set_title("Random Forest Feature Importance")

st.pyplot(fig2)

st.info(
    "Lower eye openness and deviation from baseline contribute most to higher cognitive load."
)
