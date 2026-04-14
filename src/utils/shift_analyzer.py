from app.extensions import mysql


def generate_shift_summary(user_id, shift_date):
    cur = mysql.connection.cursor()

    # 1️⃣ Fetch all eye readings for the shift
    cur.execute("""
        SELECT 
            shift_hour,
            avg_ear,
            blink_rate,
            alert_level
        FROM eye_readings
        WHERE user_id = %s AND shift_date = %s
        ORDER BY shift_hour
    """, (user_id, shift_date))

    rows = cur.fetchall()

    if not rows:
        cur.close()
        return None

    total = len(rows)

    avg_ear = sum(r["avg_ear"] for r in rows) / total
    avg_blink = sum(r["blink_rate"] for r in rows) / total

    high_hours = sum(1 for r in rows if r["alert_level"] == "High")
    critical_hours = sum(1 for r in rows if r["alert_level"] == "Critical")

    # Peak fatigue hour
    fatigue_rank = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    peak = max(rows, key=lambda r: fatigue_rank[r["alert_level"]])
    peak_hour = peak["shift_hour"]

    # 2️⃣ Final State Decision
    if critical_hours >= 1 or high_hours >= 2:
        final_state = "Exhausted"
    elif high_hours == 1:
        final_state = "Fatigued"
    elif avg_ear >= 0.30:
        final_state = "Fresh"
    else:
        final_state = "Normal"

    remarks = (
        f"Peak fatigue observed at hour {peak_hour}. "
        f"Total high fatigue hours: {high_hours}, "
        f"critical fatigue hours: {critical_hours}."
    )

    # 3️⃣ Insert / Update summary
    cur.execute("""
        INSERT INTO shift_summary (
            user_id, shift_date,
            avg_ear, avg_blink_rate,
            total_records,
            high_fatigue_hours, critical_fatigue_hours,
            peak_fatigue_hour,
            final_state, remarks
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            avg_ear = VALUES(avg_ear),
            avg_blink_rate = VALUES(avg_blink_rate),
            total_records = VALUES(total_records),
            high_fatigue_hours = VALUES(high_fatigue_hours),
            critical_fatigue_hours = VALUES(critical_fatigue_hours),
            peak_fatigue_hour = VALUES(peak_fatigue_hour),
            final_state = VALUES(final_state),
            remarks = VALUES(remarks)
    """, (
        user_id, shift_date,
        round(avg_ear, 3), round(avg_blink, 2),
        total, high_hours, critical_hours,
        peak_hour, final_state, remarks
    ))

    mysql.connection.commit()
    cur.close()

    return final_state
