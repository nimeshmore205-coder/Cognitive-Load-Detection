import time
from collections import deque

class BlinkRateTracker:
    def __init__(self, window_sec=60):
        self.window_sec = window_sec
        self.blink_times = deque()
        self._start_time = time.time()

    def update(self, blink_detected):
        current_time = time.time()

        if blink_detected:
            self.blink_times.append(current_time)

        # Remove old blinks outside window
        while self.blink_times and (current_time - self.blink_times[0]) > self.window_sec:
            self.blink_times.popleft()

    def get_blink_rate(self):
        """Return blinks per minute. Uses actual elapsed time when < window_sec
        to prevent wild extrapolation at the start of a session."""
        elapsed = time.time() - self._start_time
        # Use the smaller of elapsed or window_sec as the effective window
        effective_window = min(elapsed, self.window_sec)
        if effective_window < 5:
            # Not enough data yet — return 0 rather than a noisy extrapolation
            return 0.0
        return len(self.blink_times) * (60.0 / effective_window)
