import time
from collections import deque
import numpy as np

class FatigueTrendTracker:
    def __init__(self, window_sec=120):
        self.window_sec = window_sec
        self.values = deque()  # (timestamp, load_score)

    def update(self, load_score):
        now = time.time()
        self.values.append((now, load_score))

        # Remove old values
        while self.values and (now - self.values[0][0]) > self.window_sec:
            self.values.popleft()

    def get_trend(self):
        if len(self.values) < 5:
            return "Collecting"

        times = np.array([t for t, _ in self.values])
        scores = np.array([s for _, s in self.values])

        # Normalize time
        times = times - times[0]

        # Linear trend (slope)
        slope = np.polyfit(times, scores, 1)[0]

        if slope > 0.05:
            return "Increasing"
        elif slope < -0.05:
            return "Decreasing"
        else:
            return "Stable"
