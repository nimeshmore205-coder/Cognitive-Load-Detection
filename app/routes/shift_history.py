from flask import Blueprint, render_template, session, redirect, url_for
from app.extensions import mysql

shift_history_bp = Blueprint("shift_history", __name__, url_prefix="/user")


# ============================
# USER SHIFT HISTORY PAGE
# ============================
@shift_history_bp.route("/history")
def user_history():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            shift_date,
            avg_ear,
            avg_blink_rate,
            high_fatigue_hours,
            critical_fatigue_hours,
            final_state
        FROM shift_summary
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    shifts = cur.fetchall()
    cur.close()

    return render_template(
        "user/shift_history.html",
        shifts=shifts
    )
