from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from app.models import User, Role
from app.utils.security import verify_password
from .forms import LoginForm

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates"
)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_active and verify_password(user.password, form.password.data):
            login_user(user)

            # ambil role name dari tabel roles
            role = Role.query.filter_by(role_id=user.role_id).first()
            role_name = role.role_name if role else None

            # redirect sesuai role
            if role_name == "Customer Service":       # RL0001
                return redirect("/cs/dashboard")
            elif role_name == "Supervisor":           # RL0002
                return redirect("/spv/dashboard")
            else:
                flash("Role not recognized", "error")
                return redirect(url_for("auth.login"))

        flash("Invalid credentials or inactive account", "error")
    return render_template("login.html", form=form)



@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/request-access")
def request_access():
    return render_template("request_access.html")