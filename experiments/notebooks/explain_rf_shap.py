import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt

# ==============================
# Load model & data
# ==============================
model, label_encoder = joblib.load("models/random_forest_cognitive_load.pkl")
df = pd.read_csv("data/processed/features.csv")

features = [
    "avg_ear",
    "blink_rate",
    "ear_deviation",
    "blink_rate_deviation"
]

X = df[features]

# ==============================
# SHAP Explainer (NEW API)
# ==============================
explainer = shap.Explainer(model, X)
shap_values = explainer(X)

print("SHAP values shape:", shap_values.values.shape)
# Expected: (num_samples, num_features, num_classes)

# ==============================
# GLOBAL EXPLANATION
# ==============================
shap.summary_plot(
    shap_values.values[:, :, 0],   # class 0 (Low)
    X,
    feature_names=features,
    show=True
)

# ==============================
# LOCAL EXPLANATION (SAFE)
# ==============================
sample_index = min(100, len(X) - 1)

pred_class = model.predict(X.iloc[[sample_index]])[0]
pred_label = label_encoder.inverse_transform([pred_class])[0]

print(f"Explaining sample {sample_index}, predicted as {pred_label}")

shap.plots.waterfall(
    shap_values[sample_index, :, pred_class],
    max_display=10
)
