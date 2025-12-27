# app/cs/routes.py

import os
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.extensions import db
from app.models.workstation import Workstation
from app.models.service_record import ServiceRecord
from app.models.sop_service import SOPService
from app.models.sop_step import SOPStep

cs_bp = Blueprint("cs", __name__, template_folder="templates")


# =========================================
# CS DASHBOARD
# =========================================
@cs_bp.route("/dashboard")
@login_required
def dashboard():
    # 1️⃣ Get workstation ID from env
    ws_id = os.getenv("WORKSTATION_ID")

    workstation = (
        db.session.query(Workstation)
        .filter_by(workstation_id=ws_id)
        .first()
    )

    if workstation:
        workstation.is_active = True
        db.session.commit()

    # 2️⃣ DB-authoritative active session
    active_session = (
        db.session.query(ServiceRecord)
        .filter(
            ServiceRecord.workstation_id == ws_id,
            ServiceRecord.end_time.is_(None)
        )
        .order_by(ServiceRecord.start_time.desc())
        .first()
    )

    return render_template(
        "cs/dashboard.html",
        workstation=workstation,
        active_session=active_session
    )


# =========================================
# SERVICE GUIDELINES (STATIC SOP VIEW)
# =========================================
@cs_bp.route("/service-guidelines")
@login_required
def service_guidelines():
    services = db.session.query(SOPService).all()
    steps = (
        db.session.query(SOPStep)
        .order_by(SOPStep.step_number.asc())
        .all()
    )

    return render_template(
        "cs/service-guidelines.html",
        services=services,
        steps=steps
    )


# =========================================
# MY HISTORY
# =========================================
@cs_bp.route("/my-history")
@login_required
def my_history():
    history = (
        db.session.query(ServiceRecord)
        .filter_by(user_id=current_user.user_id)
        .order_by(ServiceRecord.start_time.desc())
        .all()
    )

    return render_template("cs/my-history.html", history=history)
