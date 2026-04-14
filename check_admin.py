from app.app import create_app
from app.extensions import mysql
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    cur = mysql.connection.cursor()
    
    print("Checking for admin users...")
    cur.execute("SELECT id, name, email, role FROM users WHERE role='admin'")
    admins = cur.fetchall()
    
    if admins:
        print("\n✅ Found existing admins:")
        for a in admins:
            print(f" - ID: {a['id']}, Name: {a['name']}, Email: {a['email']}")
        print("\n(Passwords are hashed and cannot be retrieved directly)")
    else:
        print("\n❌ No admin users found.")
        print("Creating default admin...")
        
        email = "admin@company.com"
        password = "admin123"
        hashed = generate_password_hash(password)
        
        try:
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Admin User", email, hashed, "admin")
            )
            mysql.connection.commit()
            print(f"\n✅ Created default admin:\nEmail: {email}\nPassword: {password}")
        except Exception as e:
            print(f"Error creating admin: {e}")

    cur.close()
