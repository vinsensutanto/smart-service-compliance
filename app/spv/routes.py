from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models.user import User
from app.models.workstation import Workstation
from app.models.service_record import ServiceRecord
from sqlalchemy import func
from datetime import datetime, timezone

spv_bp = Blueprint(
    "spv",
    __name__,
    template_folder="templates"
)


@spv_bp.route("/dashboard")
def dashboard():
    today = datetime.now(timezone.utc).date()

    total_sessions = (
        db.session.query(ServiceRecord)
        .filter(func.date(ServiceRecord.start_time) == today)
        .count()
    )

    stations = (
        db.session.query(
            Workstation,
            ServiceRecord,
            User
        )
        .outerjoin(
            ServiceRecord,
            (ServiceRecord.workstation_id == Workstation.workstation_id)
            & (ServiceRecord.end_time.is_(None))
        )
        .outerjoin(
            User,
            ServiceRecord.user_id == User.user_id
        )
        .order_by(Workstation.workstation_id)
        .all()
    )

    active_ws = sum(1 for _, session, _ in stations if session is not None)

    alerts = (
        db.session.query(ServiceRecord, User)
        .join(User, ServiceRecord.user_id == User.user_id)
        .filter(
            func.date(ServiceRecord.start_time) == today,
            ServiceRecord.is_normal_flow == 0
        )
        .order_by(ServiceRecord.start_time.desc())
        .all()
    )
    
    # Debug
    for ws, sr, user in stations:
        print(
            f"[DASHBOARD] {ws.workstation_id} "
            f"session={'YES' if sr else 'NO'} "
            f"sr_id={sr.service_record_id if sr else None}"
        )

    return render_template(
        "spv/dashboard.html",
        total_sessions=total_sessions,
        stations=stations,
        active_ws=active_ws,
        alerts=alerts
    )


@spv_bp.route("/user-management")
def user_management():
    # Ambil data untuk statistik dan tabel
    all_users = User.query.all()
    pending_users = User.query.filter_by(is_active=0).all()
    active_users = User.query.filter_by(is_active=1).all()
    
    return render_template("spv/user-management.html", 
                           all_users=all_users, 
                           pending_users=pending_users, 
                           active_users=active_users)

@spv_bp.route("/approve-user/<user_id>", methods=["POST"])
def approve_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_active = 1
        db.session.commit()
        flash(f"User {user.name} has been approved!", "success")
    return redirect(url_for('spv.user_management'))

@spv_bp.route("/reject-user/<user_id>", methods=["POST"])
def reject_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user) # Langsung menghapus dari database
        db.session.commit()
        flash(f"Access request for {user.name} has been removed.", "danger")
    return redirect(url_for('spv.user_management'))