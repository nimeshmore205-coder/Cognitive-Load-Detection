from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import mysql

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            return render_template(
                "auth/register.html",
                error="All fields are required"
            )

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            return render_template(
                "auth/register.html",
                error="User already exists"
            )

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, "user")
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user or not check_password_hash(user["password"], password):
            return render_template(
                "auth/login.html",
                error="Invalid email or password"
            )

        # =========================
        # SESSION
        # =========================
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]

        # =========================
        # REDIRECT BASED ON ROLE
        # =========================
        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html")


# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# =========================
# WHO AM I (DEBUG)
# =========================
@auth_bp.route("/whoami")
def whoami():
    if "user_id" in session:
        return f"Logged in as {session['user_name']} ({session['user_role']})"
    return "Not logged in"