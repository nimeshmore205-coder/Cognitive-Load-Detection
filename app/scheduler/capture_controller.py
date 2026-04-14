import threading
import time
from src.face_detection.face_mesh import FaceMeshAnalyzer
from app.scheduler.shift_summary import ShiftSummary

# CONFIG
CAPTURE_COUNT = 8
CAPTURE_DURATION = 30
PAUSE_DURATION = 30

# GLOBAL STATE
# Structure:
# {
#   user_id: {
#       "analyzer": FaceMeshAnalyzer(),
#       "summary": ShiftSummary(user_id),
#       "thread": threading.Thread,
#       "stop_requested": False,
#       "phase": "idle",
#       "camera_active": False,
#       "capture_index": 0,
#       "remaining_seconds": 0,
#       "completed": False
#   }
# }
active_sessions = {}
sessions_lock = threading.Lock()


# =========================
# HELPER: Get Session
# =========================
def get_session_context(user_id):
    with sessions_lock:
        return active_sessions.get(user_id)


# =========================
# STATE HELPERS
# =========================

def is_camera_active(user_id):
    ctx = get_session_context(user_id)
    return ctx["camera_active"] if ctx else False


def is_session_completed(user_id):
    ctx = get_session_context(user_id)
    return ctx["completed"] if ctx else False


def get_capture_progress(user_id):
    ctx = get_session_context(user_id)
    if not ctx:
        return {
            "current": 0,
            "total": CAPTURE_COUNT,
            "completed": False,
            "remaining_seconds": 0,
            "phase": "idle"
        }
    
    return {
        "current": ctx["capture_index"],
        "total": CAPTURE_COUNT,
        "completed": ctx["completed"],
        "remaining_seconds": ctx["remaining_seconds"],
        "phase": ctx["phase"]
    }


def get_user_analyzer(user_id):
    """Returns the FaceMeshAnalyzer instance for this user, if active."""
    ctx = get_session_context(user_id)
    return ctx["analyzer"] if ctx else None


def get_active_users():
    """Returns a list of user_ids that have active sessions."""
    with sessions_lock:
        return [uid for uid, ctx in active_sessions.items() if not ctx["completed"]]


# =========================
# START / STOP CONTROLLER
# =========================

def start_capture_controller(user_id, app):
    with sessions_lock:
        if user_id in active_sessions:
            # Already running or finished?
            if not active_sessions[user_id]["completed"]:
                return # Already running
            
            # If completed, but user wants to start again?
            # We must reset.
            pass

        # INIT NEW SESSION
        active_sessions[user_id] = {
            "analyzer": FaceMeshAnalyzer(),
            "summary": ShiftSummary(user_id),
            "stop_requested": False,
            "phase": "idle",
            "camera_active": False,
            "capture_index": 0,
            "remaining_seconds": 0,
            "completed": False,
            "thread": None,
            "latest_frame": None  # Store JPEG bytes here
        }

    # START THREAD
    t = threading.Thread(
        target=_run_capture_loop,
        args=(app, user_id),
        daemon=True
    )
    
    with sessions_lock:
        active_sessions[user_id]["thread"] = t
        
    t.start()


def set_latest_frame(user_id, frame_bytes):
    with sessions_lock:
        if user_id in active_sessions:
            active_sessions[user_id]["latest_frame"] = frame_bytes
        else:
            # Create a minimal frame-only entry so admin can view before session starts
            active_sessions[user_id] = {
                "analyzer": None,
                "summary": None,
                "stop_requested": False,
                "phase": "idle",
                "camera_active": False,
                "capture_index": 0,
                "remaining_seconds": 0,
                "completed": False,
                "thread": None,
                "latest_frame": frame_bytes
            }

def get_latest_frame(user_id):
    with sessions_lock:
        ctx = active_sessions.get(user_id)
        if ctx:
            return ctx.get("latest_frame")
    return None


def stop_capture_controller(user_id):
    """Signals the capture loop to stop immediately."""
    with sessions_lock:
        if user_id in active_sessions:
            active_sessions[user_id]["stop_requested"] = True
            print(f"🛑 Stop signal received for User {user_id}. Terminating session...")


# =========================
# MAIN LOOP
# =========================

def _run_capture_loop(app, user_id):

    with app.app_context():

        for i in range(CAPTURE_COUNT):

            # --- CHECK STOP ---
            if _should_stop(user_id): break

            # ---------- CAPTURE ----------
            _update_state(user_id, phase="capture", active=True, index=i+1)
            print(f"📷 Camera OPEN ({i+1}/{CAPTURE_COUNT}) - User {user_id}")

            start = time.time()
            while time.time() - start < CAPTURE_DURATION:
                if _should_stop(user_id): break

                # Update remaining time (ceil so counter starts at 30, not 29)
                rem = max(0, int(CAPTURE_DURATION - (time.time() - start) + 0.5))
                _update_time(user_id, rem)

                # Poll latest metrics from the analyzer and add to summary
                context = get_session_context(user_id)
                if context and context["analyzer"]:
                    metrics = context["analyzer"].get_latest_metrics()
                    if metrics.get("ready"):
                        context["summary"].add_metrics(metrics)

                time.sleep(0.5)  # 0.5s ticks → smoother countdown display

            if _should_stop(user_id): break

            is_last_capture = (i == CAPTURE_COUNT - 1)

            if is_last_capture:
                # ── After the 8th (final) capture: DO NOT go to 'pause'. ──
                # Transitioning to 'pause' causes the browser to stop the webcam,
                # which cuts off the tail-end frames and metrics.
                # Stay in 'completing' (camera still active) for a brief 2s window
                # so all final frames/metrics can land before we save.
                _update_state(user_id, phase="completing", active=True)
                print(f"✅ Final capture complete. Collecting tail metrics - User {user_id}")

                for _ in range(4):  # 4 × 0.5s = 2s tail window
                    if _should_stop(user_id): break
                    context = get_session_context(user_id)
                    if context and context["analyzer"]:
                        metrics = context["analyzer"].get_latest_metrics()
                        if metrics.get("ready"):
                            context["summary"].add_metrics(metrics)
                    time.sleep(0.5)
            else:
                # ---------- PAUSE (between captures 1-7) ----------
                _update_state(user_id, phase="pause", active=False)
                print(f"⏸  Pause after capture {i+1}/{CAPTURE_COUNT} - User {user_id}")

                pause_start = time.time()
                while time.time() - pause_start < PAUSE_DURATION:
                    if _should_stop(user_id): break

                    rem = max(0, int(PAUSE_DURATION - (time.time() - pause_start) + 0.5))
                    _update_time(user_id, rem)
                    time.sleep(0.5)

            if _should_stop(user_id): break

        # ---------- FINISH ----------
        _finish_session(user_id)


def _should_stop(user_id):
    ctx = get_session_context(user_id)
    return ctx["stop_requested"] if ctx else True


def _update_state(user_id, phase=None, active=None, index=None):
    with sessions_lock:
        if user_id in active_sessions:
            if phase is not None: active_sessions[user_id]["phase"] = phase
            if active is not None: active_sessions[user_id]["camera_active"] = active
            if index is not None: active_sessions[user_id]["capture_index"] = index


def _update_time(user_id, seconds):
    with sessions_lock:
        if user_id in active_sessions:
            active_sessions[user_id]["remaining_seconds"] = seconds


def _finish_session(user_id):
    summary_to_save = None
    stop_req = False

    with sessions_lock:
        if user_id in active_sessions:
            active_sessions[user_id]["phase"] = "idle"
            active_sessions[user_id]["camera_active"] = False
            active_sessions[user_id]["remaining_seconds"] = 0
            active_sessions[user_id]["completed"] = True
            
            summary_to_save = active_sessions[user_id]["summary"]
            stop_req = active_sessions[user_id]["stop_requested"]

    print(f"🧠 Saving shift summary for User {user_id}...")
    if summary_to_save:
        summary_to_save.save()

    if stop_req:
        print(f"🛑 Session forcefully stopped - User {user_id}")
    else:
        print(f"✅ Shift completed - User {user_id}")
