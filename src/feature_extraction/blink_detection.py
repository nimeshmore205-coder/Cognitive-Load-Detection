import time

class BlinkDetector:
    def __init__(self, ear_threshold=0.24, consec_frames=1):
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        self.counter = 0
        self.total_blinks = 0
        self.last_blink_time = 0
        self.min_blink_gap = 0.15  # seconds
        self.state = "OPEN" # "OPEN" or "CLOSED"

    def update(self, ear):
        blink_detected = False
        now = time.time()

        if ear < self.ear_threshold:
            self.counter += 1
            if self.counter >= self.consec_frames and self.state == "OPEN":
                self.state = "CLOSED"
        else:
            if self.state == "CLOSED":
                # Rising edge: Eye was closed, now open
                if now - self.last_blink_time > self.min_blink_gap:
                    self.total_blinks += 1
                    self.last_blink_time = now
                    blink_detected = True
                self.state = "OPEN"
            self.counter = 0

        return blink_detected
