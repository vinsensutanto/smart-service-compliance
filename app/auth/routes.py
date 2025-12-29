from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from app.extensions import db
from app.models import User, Role
from app.utils.security import verify_password, hash_password
from .forms import LoginForm

auth_web_bp = Blueprint(
    "auth_web",
    __name__,
    template_folder="templates"
)

@auth_web_bp.route('/')
def index():
    return redirect(url_for('auth_web.login'))

@auth_web_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        print(f"[DEBUG] Login attempt: email={email}, password={'*'*len(password)}")  # masked password

        user = User.query.filter_by(email=email).first()

        if not user:
            print("[DEBUG] User not found")
        else:
            print(f"[DEBUG] Found user: {user.email}, is_active={user.is_active}, hashed_pw={user.password}")

        if user and user.is_active and verify_password(user.password, password):
            login_user(user)

            # ambil role name dari tabel roles
            role = Role.query.filter_by(role_id=user.role_id).first()
            role_name = role.role_name if role else None
            
            print(f"[DEBUG] Login success, role={role_name}")
            flash("Login successful! Welcome back!", "success")

            # redirect sesuai role
            if role_name == "Customer Service":       # RL0001
                return redirect("/cs/dashboard")
            elif role_name == "Supervisor":           # RL0002
                return redirect("/spv/dashboard")
            else:
                flash("Role not recognized", "error")
                return redirect(url_for("auth_web.login"))

        flash("Invalid credentials or inactive account", "error")
        print("[DEBUG] Invalid credentials or inactive account")

    elif request.method == "POST":
        # If form.validate_on_submit() fails (like missing CSRF token)
        print(f"[DEBUG] Form validation failed: {form.errors}")

    return render_template("login.html", form=form)

@auth_web_bp.route("/logout", methods=["GET", "POST"]) 
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth_web.login"))

@auth_web_bp.route("/request-access", methods=["GET", "POST"])
def request_access():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password") # Ambil password dari form

        if not name or not email or not password:
            flash("All fields are required!", "error")
            return redirect(url_for("auth_web.request_access"))
        
        if not password or len(password) < 6:
            flash("Password must be at least 6 characters long!", "error")
            return redirect(url_for("auth_web.request_access"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "warning")
            return redirect(url_for("auth_web.request_access"))

        # Generate User ID (US + 4 digit)
        user_count = User.query.count()
        new_id = f"US{str(user_count + 1).zfill(4)}"

        # Hash password sebelum simpan ke DB
        hashed_pw = hash_password(password)

        new_user = User(
            user_id=new_id,
            role_id="RL0001", # Default: Customer Service
            name=name,
            email=email,
            password=hashed_pw,
            is_active=0 # Tetap non-aktif sampai di-approve SPV
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Request sent! Account will be active after Supervisor approval.", "success")
            return redirect(url_for("auth_web.login"))
        except Exception as e:
            db.session.rollback()
            flash("Database error. Please try again.", "error")
            print(f"Error: {e}")

    return render_template("request_access.html")

@auth_web_bp.route("/test-trigger-sop")
def test_trigger_sop():
    from app.extensions import socketio
    
    dummy_payload = {
        "service_record_id": "SESSION-DEBUG-123",
        "service": "PEMBUKAAN REKENING BARU",
        "confidence": 0.98,
        "sop": [
            { "step_id": "S01", "description": "Menyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramahMenyapa nasabah dengan ramah", "checked": False },
            { "step_id": "S02", "description": "Meminta KTP", "checked": False },
            { "step_id": "S03", "description": "Input data ke sistem", "checked": False },
            { "step_id": "S04", "description": "Menyapa nasabah dengan ramah", "checked": False },
            { "step_id": "S05", "description": "Meminta KTP", "checked": False }
        ]
        
    }

    socketio.emit("sop_update", dummy_payload, namespace="/")
    return "Data dummy berhasil ditembak ke dashboard!"