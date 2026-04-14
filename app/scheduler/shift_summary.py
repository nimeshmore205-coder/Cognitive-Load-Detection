from datetime import date, datetime
from collections import defaultdict
from app.extensions import mysql


class ShiftSummary:
    def __init__(self, user_id):
        self.user_id = user_id
        self.shift_date = date.today()
        self.samples = []


    # =========================
    # COLLECT METRICS
    # =========================
    def add_metrics(self, metrics):
        if not metrics or not metrics.get("ready"):
            return

        self.samples.append({
            "ear": metrics["ear"],
            "blink_rate": metrics["blink_rate"],
            "alert": metrics["alert_level"],
            "timestamp": datetime.now()
        })



    # =========================
    # SAVE SUMMARY
    # =========================
    def save(self):
        if not self.samples:
            print("❌ No samples collected. Summary not saved.")
            return

        total = len(self.samples)

        avg_ear = sum(s["ear"] for s in self.samples) / total
        avg_blink_rate = sum(s["blink_rate"] for s in self.samples) / total

        # ---------- SEVERITY MAP ----------
        severity_map = {
            "Low": 0,
            "Medium": 1,
            "High": 2,
            "Critical": 3
        }

        # ---------- FATIGUE COUNTS ----------
        high_fatigue_hours = sum(
            1 for s in self.samples if s["alert"] == "High"
        )
        critical_fatigue_hours = sum(
            1 for s in self.samples if s["alert"] == "Critical"
        )

        # ---------- PEAK FATIGUE HOUR (FIXED) ----------
        hour_severity = defaultdict(int)

        for s in self.samples:
            hour = s["timestamp"].hour          # 0–23 ✅
            hour_severity[hour] += severity_map.get(s["alert"], 0)

        peak_fatigue_hour = (
            max(hour_severity, key=hour_severity.get)
            if hour_severity else None
        )

        # ---------- FINAL STATE ----------
        if critical_fatigue_hours > 0:
            final_state = "Exhausted"
            remarks = "Critical fatigue detected during shift."
        elif high_fatigue_hours >= 3:
            final_state = "Fatigued"
            remarks = "Sustained high cognitive load observed."
        elif avg_blink_rate < 10:
            final_state = "Fresh"
            remarks = "User remained alert and fresh."
        else:
            final_state = "Normal"
            remarks = "Normal cognitive workload."

        # ---------- DB INSERT ----------
        cur = mysql.connection.cursor()


        cur.execute(
            """
            INSERT INTO shift_summary (
                user_id,
                shift_date,
                avg_ear,
                avg_blink_rate,
                total_records,
                high_fatigue_hours,
                critical_fatigue_hours,
                peak_fatigue_hour,
                final_state,
                remarks
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                avg_ear=VALUES(avg_ear),
                avg_blink_rate=VALUES(avg_blink_rate),
                total_records=VALUES(total_records),
                high_fatigue_hours=VALUES(high_fatigue_hours),
                critical_fatigue_hours=VALUES(critical_fatigue_hours),
                peak_fatigue_hour=VALUES(peak_fatigue_hour),
                final_state=VALUES(final_state),
                remarks=VALUES(remarks)
            """,
            (
                self.user_id,
                self.shift_date,
                round(avg_ear, 3),
                round(avg_blink_rate, 2),
                total,
                high_fatigue_hours,
                critical_fatigue_hours,
                peak_fatigue_hour,
                final_state,
                remarks,
            )
        )

        mysql.connection.commit()
        cur.close()

        print("✅ Shift summary saved successfully")
