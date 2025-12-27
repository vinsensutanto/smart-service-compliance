from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from app.models import User, Role
from app.utils.security import verify_password
from .forms import LoginForm
from app.extensions import socketio

auth_web_bp = Blueprint(
    "auth_web",
    __name__,
    template_folder="templates"
)

@auth_web_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_active and verify_password(user.password, form.password.data):
            login_user(user)

            # ambil role name dari tabel roles
            role = Role.query.filter_by(role_id=user.role_id).first()
            role_name = role.role_name if role else None
            
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
    return render_template("login.html", form=form)

@auth_web_bp.route("/logout", methods=["GET", "POST"]) 
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth_web.login"))


@auth_web_bp.route("/request-access")
def request_access():
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