from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.extensions import mysql

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("/check_trigger")
def check_trigger():
    if "user_id" not in session:
        return jsonify({"command": None})
    
    from app.utils.presence import tracker
    cmd = tracker.pop_command(session["user_id"])
    return jsonify({"command": cmd})


# =========================
# LOGIN CHECK
# =========================
def login_required():
    return "user_id" in session


# =========================
# USER DASHBOARD
# =========================
@user_bp.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("auth.login"))

    if session.get("user_role") != "user":
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Fetch last 7 days of shifts for wellness score
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT avg_ear, avg_blink_rate, high_fatigue_hours,
               critical_fatigue_hours, final_state, shift_date
        FROM shift_summary
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 7
    """, (user_id,))
    recent_shifts = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS total FROM shift_summary WHERE user_id = %s", (user_id,))
    total_sessions = cur.fetchone()["total"]
    cur.close()

    # Compute wellness score (0–100)
    if recent_shifts:
        score = 100
        for s in recent_shifts:
            state = (s["final_state"] or "").lower()
            if "critical" in state:
                score -= 15
            elif "high" in state or "fatigue" in state:
                score -= 8
            elif "moderate" in state:
                score -= 4
            ear = float(s["avg_ear"] or 0.3)
            if ear < 0.18:
                score -= 10
            elif ear < 0.22:
                score -= 5
        score = max(0, min(100, score))
        if score >= 75:
            wellness_label, wellness_color = "Excellent", "#13ecda"
        elif score >= 55:
            wellness_label, wellness_color = "Good", "#60a5fa"
        elif score >= 35:
            wellness_label, wellness_color = "Fair", "#f59e0b"
        else:
            wellness_label, wellness_color = "Low", "#ef4444"
    else:
        score, wellness_label, wellness_color = None, "No Data", "#6b7280"

    return render_template(
        "user/dashboard.html",
        user_name=session.get("user_name"),
        wellness_score=score,
        wellness_label=wellness_label,
        wellness_color=wellness_color,
        total_sessions=total_sessions,
        recent_shifts=recent_shifts,
    )


# =========================
# USER PROFILE
# =========================
@user_bp.route("/profile")
def profile():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT name, email, role, created_at, address
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cur.fetchone()
    cur.close()

    return render_template(
        "user/profile.html",
        user=user
    )


# =========================
# EDIT PROFILE
# =========================
@user_bp.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        address = request.form.get("address")

        # Validation (basic)
        if not name or not email:
            cur.close()
            return render_template("user/edit_profile.html", error="Name and Email are required", user={"name": name, "email": email, "address": address})

        # Update user
        try:
            cur.execute("""
                UPDATE users
                SET name=%s, email=%s, address=%s
                WHERE id=%s
            """, (name, email, address, user_id))
            mysql.connection.commit()
            
            # Update session if name changed
            session["user_name"] = name
            
            cur.close()
            return redirect(url_for("user.profile"))
            
        except Exception as e:
            mysql.connection.rollback()
            cur.close()
            # Handle duplicate email or other errors
            return render_template("user/edit_profile.html", error=f"Error updating profile: {e}", user={"name": name, "email": email, "address": address})

    # GET request - fetch current data
    cur.execute("SELECT name, email, address FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template("user/edit_profile.html", user=user)


@user_bp.route("/stress_relief")
def stress_relief():
    if not login_required():
        return redirect(url_for("auth.login"))
    return render_template("user/stress_relief.html")
