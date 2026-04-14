from datetime import datetime
from app.extensions import mysql


# =====================================
# LIVE (PER-SECOND) INSERT
# =====================================
def save_live_eye_reading(
    user_id,
    avg_ear,
    blink_rate,
    blink_10s,
    rule_load,
    rf_load,
    lstm_load,
    alert_level
):
    now = datetime.now()

    cur = mysql.connection.cursor()
    cur.execute(
        """
        INSERT INTO eye_readings (
            user_id,
            shift_date,
            shift_hour,
            avg_ear,
            blink_rate,
            blink_10s,
            rule_load,
            rf_load,
            lstm_load,
            alert_level
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            user_id,
            now.date(),
            now.hour,
            avg_ear,
            blink_rate,
            blink_10s,
            rule_load,
            rf_load,
            lstm_load,
            alert_level
        )
    )

    mysql.connection.commit()
    cur.close()


# =====================================
# 30-SECOND AGGREGATED INSERT
# =====================================
def save_hourly_eye_reading(
    user_id,
    shift_date,
    shift_hour,
    avg_ear,
    avg_blink_rate,
    max_blink_10s,
    rule_load,
    rf_load,
    lstm_load,
    alert_level
):
    cur = mysql.connection.cursor()
    cur.execute(
        """
        INSERT INTO eye_readings (
            user_id,
            shift_date,
            shift_hour,
            avg_ear,
            blink_rate,
            blink_10s,
            rule_load,
            rf_load,
            lstm_load,
            alert_level
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            user_id,
            shift_date,
            shift_hour,
            avg_ear,
            avg_blink_rate,
            max_blink_10s,
            rule_load,
            rf_load,
            lstm_load,
            alert_level
        )
    )

    mysql.connection.commit()
    cur.close()
