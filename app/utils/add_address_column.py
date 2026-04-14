
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask import Flask
from flask_mysqldb import MySQL
from app.extensions import mysql

def migrate():
    app = Flask(__name__)
    
    # Configure MySQL from environment variables or hardcoded values (matching config in app.py or similar)
    # Since I don't see config.py, I'll assume standard defaults or try to load from app factory if possible.
    # However, for a simple script, it's often easier to just ask the user or try to import the app.
    
    from app import create_app
    app = create_app()

    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            print("Checking if 'address' column exists in 'users' table...")
            
            # Check if column exists
            cur.execute("""
                SELECT count(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'address'
            """)
            
            exists = cur.fetchone()[0]
            
            if not exists:
                print("Column 'address' not found. Adding it...")
                cur.execute("ALTER TABLE users ADD COLUMN address TEXT")
                mysql.connection.commit()
                print("Column 'address' added successfully.")
            else:
                print("Column 'address' already exists.")
                
            cur.close()
            
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
