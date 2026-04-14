
from app.app import create_app
from app.extensions import mysql
import traceback

app = create_app()

with app.app_context():
    try:
        cur = mysql.connection.cursor()
        try:
            print("EXECUTING: ALTER TABLE users ADD COLUMN address TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN address TEXT")
            mysql.connection.commit()
            print("Successfully added 'address' column.")
        except Exception as e:
            print(f"Error adding column (might already exist): {e}")
            # traceback.print_exc()
        
        cur.close()
    except Exception as e:
        print(f"Connection/Cursor Error: {e}")
