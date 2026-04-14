# import time
# from threading import Thread
# from datetime import datetime

# from app.routes.live_routes import camera_state, state_lock
# from src.face_detection.face_mesh import get_latest_metrics
# from app.utils.eye_logger import save_hourly_eye_reading
# from app.utils.eye_logger import save_hourly_eye_reading

# CAPTURE_DURATION = 30  # seconds
# INTERVAL = 60          # every 1 minute (test mode)


# def run_hourly_capture(app):
#     while True:
#         print("⏳ Waiting for next capture window...")
#         time.sleep(INTERVAL)

#         with state_lock:
#             camera_state["active"] = True

#         print("📸 Capture window STARTED")

#         samples = []
#         start = time.time()

#         while time.time() - start < CAPTURE_DURATION:
#             metrics = get_latest_metrics()
#             if metrics["rule"] != "Calibrating":
#                 samples.append(metrics)
#             time.sleep(1)

#         with state_lock:
#             camera_state["active"] = False

#         print("✅ Capture window ENDED")

#         if not samples:
#             continue

#         avg_ear = sum(m["ear"] for m in samples) / len(samples)
#         avg_blink = sum(m["blink_rate"] for m in samples) / len(samples)

#         now = datetime.now()

#         save_hourly_eye_reading(
#             user_id=1,
#             shift_date=now.date(),
#             shift_hour=now.hour,
#             avg_ear=avg_ear,
#             avg_blink_rate=avg_blink,
#             avg_blink_10s=max(m["blink_10s"] for m in samples),
#             rule_load=samples[-1]["rule"],
#             rf_load=samples[-1]["rf"],
#             lstm_load=samples[-1]["lstm"],
#             alert_level=samples[-1]["alert_level"]
#         )
