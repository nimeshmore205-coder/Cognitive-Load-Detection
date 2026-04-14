from app.extensions import mysql

def save_fatigue_alert(user_id, model, load_label, ear, blink_rate):
    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO fatigue_alerts (user_id, model, load_label, ear, blink_rate)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, model, load_label, ear, blink_rate))

    mysql.connection.commit()
    cur.close()
