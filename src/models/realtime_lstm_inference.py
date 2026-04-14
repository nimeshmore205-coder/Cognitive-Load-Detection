import numpy as np
import joblib
from tensorflow.keras.models import load_model
from collections import deque


class RealtimeLSTMCognitiveLoad:
    def __init__(self, model_path, scaler_path, label_encoder_path, seq_len=30):
        self.model = load_model(model_path)
        self.scaler = joblib.load(scaler_path)
        self.label_encoder = joblib.load(label_encoder_path)

        self.seq_len = seq_len
        self.buffer = deque(maxlen=seq_len)

    def update(self, feature_vector):
        """
        feature_vector = [avg_ear, blink_rate, ear_dev, blink_dev]
        """
        scaled = self.scaler.transform([feature_vector])[0]
        self.buffer.append(scaled)

        if len(self.buffer) < self.seq_len:
            return None  # not enough data yet

        X = np.array(self.buffer).reshape(1, self.seq_len, -1)
        probs = self.model.predict(X, verbose=0)[0]
        idx = np.argmax(probs)

        return self.label_encoder.inverse_transform([idx])[0]
