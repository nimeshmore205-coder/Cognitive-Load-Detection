from flask import Blueprint, send_file, session
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from app.extensions import mysql
import os

shift_report_bp = Blueprint(
    "shift_report",
    __name__,
    url_prefix="/live/shift_report"
)


@shift_report_bp.route("/pdf")
def download_shift_report():

    # ---------------- AUTH ----------------
    if "user_id" not in session:
        return "Unauthorized", 401

    uid = session["user_id"]

    # ---------------- FETCH DATA ----------------
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            user_id,
            shift_date,
            avg_ear,
            avg_blink_rate,
            high_fatigue_hours,
            critical_fatigue_hours,
            final_state,
            remarks,
            created_at
        FROM shift_summary
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (uid,))

    row = cur.fetchone()
    cur.close()

    if not row:
        return "No shift summary found", 404

    # ---------------- HANDLE BOTH DICT & TUPLE ----------------
    if isinstance(row, dict):
        user_id          = row["user_id"]
        shift_date       = row["shift_date"]
        avg_ear          = row["avg_ear"]
        avg_blink_rate   = row["avg_blink_rate"]
        high_fatigue     = row["high_fatigue_hours"]
        critical_fatigue = row["critical_fatigue_hours"]
        final_state      = row["final_state"]
        remarks          = row["remarks"]
        created_at       = row["created_at"]
    else:
        user_id          = row[0]
        shift_date       = row[1]
        avg_ear          = row[2]
        avg_blink_rate   = row[3]
        high_fatigue     = row[4]
        critical_fatigue = row[5]
        final_state      = row[6]
        remarks          = row[7]
        created_at       = row[8]

    # ---------------- SAFE CONVERSIONS ----------------
    avg_ear = float(avg_ear or 0)
    avg_blink_rate = float(avg_blink_rate or 0)
    high_fatigue = int(high_fatigue or 0)
    critical_fatigue = int(critical_fatigue or 0)

    # ---------------- FILE PATH ----------------
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    os.makedirs(STATIC_DIR, exist_ok=True)

    filepath = os.path.join(STATIC_DIR, "shift_report.pdf")

    # ---------------- BUILD PDF ----------------
    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()
    title = styles["Title"]
    body = styles["BodyText"]

    elements = []

    elements.append(Paragraph("Cognitive Load Shift Report", title))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"User ID: {user_id}", body))
    elements.append(Paragraph(f"Shift Date: {shift_date}", body))
    elements.append(Paragraph(f"Generated At: {created_at}", body))

    elements.append(Spacer(1, 15))

    elements.append(Paragraph(f"Average EAR: {round(avg_ear,3)}", body))
    elements.append(Paragraph(f"Average Blink Rate: {round(avg_blink_rate,2)}", body))

    elements.append(Spacer(1, 15))

    elements.append(Paragraph(f"High Fatigue Count: {high_fatigue}", body))
    elements.append(Paragraph(f"Critical Fatigue Count: {critical_fatigue}", body))

    elements.append(Spacer(1, 15))

    elements.append(Paragraph(f"Final State: {final_state}", body))
    elements.append(Paragraph(f"Remarks: {remarks}", body))

    doc.build(elements)

    return send_file(filepath, as_attachment=True)
