from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash
from app.models import User, AccessRequest
from app.extensions import db
from .forms import LoginForm, RequestAccessForm

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_active and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect("/cs/dashboard" if user.role == "cs" else "/spv/dashboard")
        flash("Invalid credentials or inactive account", "error")
    return render_template("auth/login.html", form=form)

@auth_bp.route("/request-access", methods=["GET", "POST"])
def request_access():
    form = RequestAccessForm()
    if form.validate_on_submit():
        req = AccessRequest(
            name=form.name.data,
            email=form.email.data,
            reason=form.reason.data
        )
        db.session.add(req)
        db.session.commit()
        flash("Access request submitted successfully", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/request_access.html", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
