import csv
import os
import time

class DataLogger:
    def __init__(self, file_path):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        self.file_exists = os.path.isfile(file_path)

        self.csv_file = open(file_path, mode="a", newline="")
        self.writer = csv.writer(self.csv_file)

        if not self.file_exists:
            self.writer.writerow([
                "timestamp",
                "avg_ear",
                "blink_detected",
                "blink_rate",
                "baseline_ear",
                "baseline_blink_rate",
                "ear_deviation",
                "blink_rate_deviation"
            ])

    def log(self, avg_ear, blink_detected, blink_rate,
            baseline_ear, baseline_blink_rate):

        timestamp = time.time()

        ear_dev = avg_ear - baseline_ear
        blink_dev = blink_rate - baseline_blink_rate

        self.writer.writerow([
            timestamp,
            round(avg_ear, 4),
            int(blink_detected),
            round(blink_rate, 2),
            round(baseline_ear, 4),
            round(baseline_blink_rate, 2),
            round(ear_dev, 4),
            round(blink_dev, 2)
        ])

        self.csv_file.flush()

    def close(self):
        self.csv_file.close()
