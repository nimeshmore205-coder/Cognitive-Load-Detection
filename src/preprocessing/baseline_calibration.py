import time
import json
import os

class BaselineCalibrator:
    def __init__(self, duration_sec=60):
        self.duration_sec = duration_sec
        self.ear_values = []
        self.blink_count = 0
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def update(self, ear, blink_detected):
        self.ear_values.append(ear)
        if blink_detected:
            self.blink_count += 1

    def is_complete(self):
        return (time.time() - self.start_time) >= self.duration_sec

    def compute_baseline(self):
        avg_ear = sum(self.ear_values) / len(self.ear_values)
        blink_rate = (self.blink_count / self.duration_sec) * 60

        return {
            "avg_ear": round(avg_ear, 4),
            "blink_rate": round(blink_rate, 2)
        }

    def save(self, baseline_data, save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(baseline_data, f, indent=4)
