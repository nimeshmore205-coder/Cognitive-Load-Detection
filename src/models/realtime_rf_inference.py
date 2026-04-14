import joblib
import numpy as np

class RealtimeRFCognitiveLoad:
    def __init__(self, model_path):
        self.model, self.label_encoder = joblib.load(model_path)

    def predict(self, avg_ear, blink_rate, ear_dev, blink_dev):
        X = np.array([[avg_ear, blink_rate, ear_dev, blink_dev]])
        pred = self.model.predict(X)[0]
        label = self.label_encoder.inverse_transform([pred])[0]
        return label
