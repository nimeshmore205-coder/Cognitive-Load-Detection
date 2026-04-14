from flask import Blueprint, Response, session, redirect, url_for, render_template, jsonify, current_app, request
import cv2
import time
import numpy as np

from app.scheduler.capture_controller import (
    is_camera_active,
    get_capture_progress,
    start_capture_controller,
    stop_capture_controller,
    get_user_analyzer,
    set_latest_frame,
    get_latest_frame
)

live_bp = Blueprint("live", __name__, url_prefix="/live")


@live_bp.route("/monitor")
def monitor():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    real_app = current_app._get_current_object()
    user_id = session["user_id"]

    # ✅ SAFE: starts only once per shift
    start_capture_controller(
        user_id=user_id,
        app=real_app
    )

    return render_template("live/monitor.html")


@live_bp.route("/camera_state")
def camera_state():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(get_capture_progress(session["user_id"]))


@live_bp.route("/stop_capture", methods=["POST"])
def stop_capture():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    stop_capture_controller(session["user_id"])
    return jsonify({"status": "Stopping capture session"})


@live_bp.route("/upload_frame", methods=["POST"])
def upload_frame():
    """
    Receives a JPEG frame from the USER's browser (via getUserMedia + canvas.toBlob)
    and stores it in the shared buffer so the admin can view it.
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    file = request.files.get("frame")
    if not file:
        return jsonify({"error": "No frame"}), 400

    # Read raw JPEG bytes
    frame_bytes = file.read()

    # Optionally run face analysis on this frame
    from app.scheduler.capture_controller import get_user_analyzer
    analyzer = get_user_analyzer(user_id)
    if analyzer:
        try:
            # Decode JPEG → numpy → process → re-encode
            nparr = np.frombuffer(frame_bytes, np.uint8)
            img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                img = analyzer.process_frame(img)
                ret, buf = cv2.imencode(".jpg", img)
                if ret:
                    frame_bytes = buf.tobytes()
        except Exception as e:
            print(f"Frame analysis error: {e}")

    # Store in shared buffer (admin reads from here)
    set_latest_frame(user_id, frame_bytes)
    return jsonify({"ok": True})


@live_bp.route("/check_command")
def check_command():
    """
    User's browser polls this to discover admin commands (e.g. START_MONITORING).
    Returns and clears the pending command.
    """
    if "user_id" not in session:
        return jsonify({"command": None})

    from app.utils.presence import tracker
    user_id = session["user_id"]
    tracker.update_seen(user_id)  # keep presence alive
    cmd = tracker.pop_command(user_id)
    return jsonify({"command": cmd})


@live_bp.route("/metrics")
def live_metrics():
    if "user_id" not in session:
        return jsonify({"ready": False})

    analyzer = get_user_analyzer(session["user_id"])
    if not analyzer:
        return jsonify({"ready": False})

    data = analyzer.get_latest_metrics()

    if not data or not data.get("ready"):
        return jsonify({"ready": False})

    return jsonify({
        "ready": True,
        "ear": round(data["ear"], 3),
        "blink_10s": data["blink_10s"],
        "blink_rate": data["blink_rate"],
        "rule": data["rule"],
        "rf": data["rf"],
        "lstm": data["lstm"],
        "alert": data["alert_level"],
    })


@live_bp.route("/video_feed")
def video_feed():
    """
    Legacy route – now serves the shared buffer frames captured client-side.
    The user's own browser can use this to see a preview, or admin fallback.
    """
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return Response(
        generate_admin_frames(session["user_id"]),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def generate_frames(user_id):
    cap = None

    while True:
        if is_camera_active(user_id):
            if cap is None:
                cap = cv2.VideoCapture(0)
                print(f"📷 Camera OPEN (stream) - User {user_id}")

            success, frame = cap.read()
            if not success:
                continue

            # Process with User's Analyzer
            analyzer = get_user_analyzer(user_id)
            if analyzer:
                frame = analyzer.process_frame(frame)

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            
            # SAVE FOR ADMIN
            from app.scheduler.capture_controller import set_latest_frame
            set_latest_frame(user_id, frame_bytes)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

            time.sleep(0.03)

        else:
            if cap is not None:
                cap.release()
                cap = None
                print(f"🛑 Camera CLOSED (stream) - User {user_id}")

            time.sleep(0.5)  # 🔒 stabilizer


def generate_admin_frames(user_id):
    """
    Streams the LATEST frame uploaded by the user's browser.
    Reads from the shared buffer - no server webcam access.
    Works during both 'capture' and 'pause' phases.
    """
    no_frame_count = 0
    
    while True:
        frame_bytes = get_latest_frame(user_id)
        
        if frame_bytes:
            no_frame_count = 0
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )
            time.sleep(0.04)  # ~25 fps max
        else:
            no_frame_count += 1
            time.sleep(0.2)   # Wait for user to start uploading frames
            if no_frame_count % 25 == 0:
                print(f"⏳ Admin waiting for frames from user {user_id}...")
