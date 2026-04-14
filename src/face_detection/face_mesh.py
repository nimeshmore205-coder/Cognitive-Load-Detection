"""
face_mesh.py
Reusable face + cognitive load inference logic
SAFE to import inside Flask OR standalone
"""

import cv2
import os
import time
import numpy as np

from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision.core.image import Image
from mediapipe.tasks.python.vision.core.image import ImageFormat

from src.feature_extraction.ear_calculation import calculate_ear
from src.feature_extraction.blink_detection import BlinkDetector
from src.feature_extraction.blink_rate import BlinkRateTracker
from src.preprocessing.baseline_calibration import BaselineCalibrator

from models.cognitive_load_score import compute_cognitive_load
from src.models.realtime_rf_inference import RealtimeRFCognitiveLoad
from src.models.realtime_lstm_inference import RealtimeLSTMCognitiveLoad


# PATHS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FACE_MODEL_PATH = os.path.join(BASE_DIR, "models", "face_landmarker.task")
RF_MODEL_PATH = os.path.join(BASE_DIR, "models", "random_forest_cognitive_load.pkl")
LSTM_MODEL_PATH = os.path.join(BASE_DIR, "models", "lstm_cognitive_load.h5")
LSTM_SCALER_PATH = os.path.join(BASE_DIR, "models", "lstm_scaler.pkl")
LSTM_ENCODER_PATH = os.path.join(BASE_DIR, "models", "lstm_label_encoder.pkl")


# HELPER: Convert landmarks → (x, y)
def lm_xy(lm):
    return np.array([lm.x, lm.y])


class FaceMeshAnalyzer:
    def __init__(self):
        # LOAD MODELS ONCE PER INSTANCE
        self._face_options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=FACE_MODEL_PATH),
            num_faces=1
        )
        self._face_detector = vision.FaceLandmarker.create_from_options(self._face_options)

        self._blink_detector = BlinkDetector(ear_threshold=0.24, consec_frames=1)
        self._blink_rate_tracker = BlinkRateTracker(window_sec=60)
        self._recent_blinks = []

        self._baseline_calibrator = BaselineCalibrator(duration_sec=5)
        self._baseline_calibrator.start()
        self._baseline_done = False
        self._baseline = None

        self._rf_predictor = RealtimeRFCognitiveLoad(RF_MODEL_PATH)
        self._lstm_predictor = RealtimeLSTMCognitiveLoad(
            LSTM_MODEL_PATH,
            LSTM_SCALER_PATH,
            LSTM_ENCODER_PATH,
            seq_len=30
        )

        self._latest_metrics = {
            "ear": None,
            "blink_rate": None,
            "blink_10s": None,
            "rule": "Calibrating",
            "rf": "Calibrating",
            "lstm": "Calibrating",
            "alert_level": "Low",
            "ready": False
        }

        self._alert_state  = {"high_start": None}


    def compute_alert_level(self, rule, rf, lstm):
        now = time.time()
        is_high = rule == "High" or rf == "High" or lstm == "High"

        if is_high:
            if self._alert_state["high_start"] is None:
                self._alert_state["high_start"] = now

            elapsed = now - self._alert_state["high_start"]
            if elapsed >= 10:
                return "Critical"
            elif elapsed >= 5:
                return "High"
            elif elapsed >= 2:
                return "Medium"
        else:
            self._alert_state["high_start"] = None

        return "Low"


    def process_frame(self, frame):
        """
        Processes a single frame, updates internal state/metrics, and returns the annotated frame.
        """
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
        result = self._face_detector.detect(mp_image)

        if not result.face_landmarks:
            return frame

        landmarks = result.face_landmarks[0]

        # ✅ CORRECT EYE INDICES (MediaPipe standard)
        LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
        RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

        left_eye = [lm_xy(landmarks[i]) for i in LEFT_EYE_IDX]
        right_eye = [lm_xy(landmarks[i]) for i in RIGHT_EYE_IDX]

        avg_ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

        # ---------------- BLINK
        now = time.time()
        blink = self._blink_detector.update(avg_ear)

        if blink:
            self._recent_blinks.append(now)

        self._recent_blinks[:] = [t for t in self._recent_blinks if now - t <= 10]
        blink_10s = len(self._recent_blinks)

        self._blink_rate_tracker.update(blink)
        blink_rate = self._blink_rate_tracker.get_blink_rate()

        # ================= BASELINE
        if not self._baseline_done:
            self._baseline_calibrator.update(avg_ear, blink)

            remaining = int(self._baseline_calibrator.duration_sec -
                            (time.time() - self._baseline_calibrator.start_time))

            cv2.putText(frame, f"Calibrating baseline... {remaining}s",
                        (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            self._latest_metrics.update({
                "ear": round(avg_ear, 3),
                "blink_rate": round(blink_rate, 2),
                "blink_10s": blink_10s,
                "rule": "Calibrating",
                "rf": "Calibrating",
                "lstm": "Calibrating",
                "alert_level": "Low",
            })

            if self._baseline_calibrator.is_complete():
                self._baseline = self._baseline_calibrator.compute_baseline()
                self._baseline_done = True
                self._latest_metrics["ready"] = True

            return frame

        # ================= INFERENCE
        ear_base = self._baseline["avg_ear"] if self._baseline["avg_ear"] > 0 else 0.0001
        blink_base = self._baseline["blink_rate"] if self._baseline["blink_rate"] > 0 else 0.0001
        
        ear_dev = max(0, (ear_base - avg_ear) / ear_base)
        blink_dev = max(0, (blink_base - blink_rate) / blink_base)

        _, rule = compute_cognitive_load(avg_ear, blink_rate,
                                         self._baseline["avg_ear"], self._baseline["blink_rate"])
        rf = self._rf_predictor.predict(avg_ear, blink_rate, ear_dev, blink_dev)
        lstm = self._lstm_predictor.update([avg_ear, blink_rate, ear_dev, blink_dev])

        alert_level = self.compute_alert_level(rule, rf, lstm)
        
        self._latest_metrics.update({
            "ear": round(avg_ear, 3),
            "blink_rate": round(blink_rate, 2),
            "blink_10s": blink_10s,
            "rule": rule,
            "rf": rf,
            "lstm": lstm if lstm else "Collecting",
            "alert_level": alert_level,
            "ready": True
        })

        return frame


    def get_latest_metrics(self):
        return self._latest_metrics

