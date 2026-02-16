from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ========================
# SECRET KEY
# ========================
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# ========================
# DATABASE CONFIG (MariaDB / MySQL)
# ========================
DB_USER = os.getenv("DB_USER", "flaskuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "flaskpass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "login_db")   # ✅ corrected default

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ========================
# MAIL CONFIG
# ========================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

# ========================
# DATABASE MODEL
# ========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))

# ========================
# CREATE TABLES
# ========================
with app.app_context():
    db.create_all()

# ========================
# ROUTES
# ========================

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    address = request.form["address"]
    phone = request.form["phone"]
    email = request.form["email"]
    password = request.form["password"]

    # Check duplicate email
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return "Email already registered!"

    hashed_password = generate_password_hash(password)

    new_user = User(
        name=name,
        address=address,
        phone=phone,
        email=email,
        password=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    # Send Email Notification
    try:
        msg = Message(
            subject="New User Registration",
            sender=app.config['MAIL_USERNAME'],
            recipients=[os.getenv("ADMIN_EMAIL")]
        )

        msg.body = f"""
New User Registered:

Name: {name}
Address: {address}
Phone: {phone}
Email: {email}
"""
        mail.send(msg)
    except Exception as e:
        print("Mail Error:", e)

    return redirect(url_for("home"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session["user"] = user.name
        return redirect(url_for("dashboard"))
    else:
        return "Invalid Credentials"


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html")
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

