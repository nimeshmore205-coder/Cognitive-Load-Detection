from flask import Blueprint, render_template, session, redirect, url_for, jsonify, Response
from app.extensions import mysql

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# =========================
# ADMIN CHECK
# =========================
def admin_required():
    return "user_id" in session and session.get("user_role") == "admin"


# =========================
# ADMIN DASHBOARD
# =========================
@admin_bp.route("/dashboard")
def dashboard():

    if not admin_required():
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    # Total users
    cur.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cur.fetchone()["total"]

    # Total admins
    cur.execute("SELECT COUNT(*) AS admins FROM users WHERE role='admin'")
    total_admins = cur.fetchone()["admins"]

    # Total normal users
    cur.execute("SELECT COUNT(*) AS users FROM users WHERE role='user'")
    total_normal_users = cur.fetchone()["users"]

    # Total shifts
    cur.execute("SELECT COUNT(*) AS shifts FROM shift_summary")
    total_shifts = cur.fetchone()["shifts"]

    # Fatigued users count
    cur.execute("SELECT COUNT(*) AS fatigued FROM shift_summary WHERE final_state IN ('fatigued', 'critical')")
    fatigued_users = cur.fetchone()["fatigued"]

    # Recent shifts (last 10, with user name)
    cur.execute("""
        SELECT ss.user_id, u.name, ss.shift_date, ss.final_state
        FROM shift_summary ss
        JOIN users u ON ss.user_id = u.id
        ORDER BY ss.created_at DESC
        LIMIT 10
    """)
    recent_shifts_raw = cur.fetchall()
    recent_shifts = [(r["user_id"], r["name"], r["shift_date"], r["final_state"]) for r in recent_shifts_raw]

    cur.close()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_admins=total_admins,
        total_normal_users=total_normal_users,
        total_shifts=total_shifts,
        fatigued_users=fatigued_users,
        recent_shifts=recent_shifts
    )


# =========================
# VIEW ALL USERS
# =========================
@admin_bp.route("/users")
def users():

    if not admin_required():
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email, role, created_at FROM users")
    users = cur.fetchall()
    cur.close()

    return render_template("admin/users.html", users=users)


# =========================
# DELETE USER
# =========================
@admin_bp.route("/delete_user/<int:user_id>")
def delete_user(user_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    # Prevent deleting admin
    cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()

    if row and row["role"] == "admin":
        return redirect(url_for("admin.users"))

    cur.execute("DELETE FROM shift_summary WHERE user_id=%s", (user_id,))
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    mysql.connection.commit()

    cur.close()

    return redirect(url_for("admin.users"))


# =========================
# USER SHIFT HISTORY
# =========================
@admin_bp.route("/user/<int:user_id>/history")
def user_shift_history(user_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT shift_date,
               avg_ear,
               avg_blink_rate,
               high_fatigue_hours,
               critical_fatigue_hours,
               final_state,
               created_at
        FROM shift_summary
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user_id,))

    shifts = cur.fetchall()

    cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    cur.close()

    dates = [str(s["shift_date"]) for s in shifts]
    blink_rates = [float(s["avg_blink_rate"] or 0) for s in shifts]
    ears = [float(s["avg_ear"] or 0) for s in shifts]

    return render_template(
        "admin/user_shift_history.html",
        shifts=shifts,
        user_name=user["name"],
        user_id=user_id,
        dates=dates,
        blink_rates=blink_rates,
        ears=ears
    )


# =========================
# LIVE DASHBOARD (HR VIEW)
# =========================
@admin_bp.route("/live_dashboard")
def live_dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))
    
    # Get all users to show their status
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE role!='admin'")
    users = cur.fetchall()
    cur.close()

    from app.scheduler.capture_controller import get_capture_progress, is_camera_active
    from app.utils.presence import tracker

    users_status = []
    for u in users:
        uid = u["id"]
        progress = get_capture_progress(uid)
        active = is_camera_active(uid)
        is_online = tracker.is_online(uid)
        
        status = "Offline"
        status_color = "secondary"
        
        # Logic for status
        if active:
            status = "Monitoring"
            status_color = "success"
        elif progress["current"] > 0 and not progress["completed"]:
            status = "Paused"
            status_color = "warning"
        elif is_online:
            status = "Online"
            status_color = "info"
        
        if progress["completed"]:
            phase_label = "Completed"
        else:
            phase_label = progress["phase"]

        users_status.append({
            "id": uid,
            "name": u["name"],
            "email": u["email"],
            "status": status,
            "status_color": status_color,
            "is_online": is_online,
            "phase": phase_label,
            "progress": f"{progress['current']}/{progress['total']}",
            "is_completed": progress["completed"]
        })

    return render_template("admin/live_dashboard.html", users=users_status)


@admin_bp.route("/api/shift_report/latest/<int:user_id>")
def get_latest_shift_report(user_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT avg_ear, avg_blink_rate, high_fatigue_hours, critical_fatigue_hours, final_state, created_at
        FROM shift_summary
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return jsonify({"found": False, "analysis": "No completed shifts found."})

    # Generate Analysis Text
    ear = float(row["avg_ear"] or 0)
    blink = float(row["avg_blink_rate"] or 0)
    high = row["high_fatigue_hours"] or 0
    critical = row["critical_fatigue_hours"] or 0
    
    analysis = f"Employee maintained an average EAR of {ear:.2f} and Blink Rate of {blink:.1f}/min. "
    
    if critical > 0:
        analysis += f"⚠️ CRITICAL fatigue detected for {critical} instances. Immediate attention recommended."
    elif high > 0:
        analysis += f"⚠️ High fatigue signs observed for {high} instances. Monitor closely."
    else:
        analysis += "✅ Performance remained stable with no significant fatigue signs."

    return jsonify({
        "found": True,
        "ear": ear,
        "blink_rate": blink,
        "high_fatigue": high,
        "critical_fatigue": critical,
        "analysis": analysis
    })


@admin_bp.route("/trigger_monitoring/<int:user_id>", methods=["POST"])
def trigger_monitoring(user_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    from app.utils.presence import tracker
    tracker.set_command(user_id, "START_MONITORING")
    
    return jsonify({"status": "Command Sent"})


@admin_bp.route("/monitor/<int:user_id>")
def monitor_user(user_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return "User not found", 404

    return render_template("admin/monitor_user.html", user=user, user_id=user_id)


@admin_bp.route("/api/metrics/<int:user_id>")
def admin_user_metrics(user_id):
    if not admin_required():
        return jsonify({"ready": False}), 401

    from app.scheduler.capture_controller import get_user_analyzer, get_capture_progress, is_camera_active
    
    analyzer = get_user_analyzer(user_id)
    progress = get_capture_progress(user_id)
    active = is_camera_active(user_id)

    # Base response
    resp = {
        "ready": False,
        "phase": progress["phase"],
        "remaining_seconds": progress["remaining_seconds"],
        "current": progress["current"],
        "total": progress["total"],
        "completed": progress["completed"],
        "is_active": active
    }

    if not analyzer:
        resp["message"] = "User analyzer not active"
        return jsonify(resp)

    data = analyzer.get_latest_metrics()
    if not data or not data.get("ready"):
        return jsonify(resp)

    resp.update({
        "ready": True,
        "ear": round(data["ear"], 3),
        "blink_10s": data["blink_10s"],
        "blink_rate": data["blink_rate"],
        "rule": data["rule"],
        "rf": data["rf"],
        "lstm": data["lstm"],
        "alert": data["alert_level"],
    })

    return jsonify(resp)


@admin_bp.route("/video_feed/<int:user_id>")
def admin_video_feed(user_id):
    if not admin_required():
        return "Unauthorized", 401

    # Reuse the generator from live_routes but for specific user
    from app.routes.live_routes import generate_admin_frames
    
    # Use the passive generator that reads shared memory
    return Response(
        generate_admin_frames(user_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
