# app/cs/routes.py

import os
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.extensions import db
from app.models.workstation import Workstation
from app.models.service_record import ServiceRecord
from app.models.sop_service import SOPService
from app.models.sop_step import SOPStep
from app.models.service_checklist import ServiceChecklist
from app.extensions import socketio
from app.services import session_manager

cs_bp = Blueprint("cs", __name__, template_folder="templates")


# =========================================
# CS DASHBOARD
# =========================================
@cs_bp.route("/dashboard")
@login_required
def dashboard():
    active_session = (
        db.session.query(ServiceRecord)
        .filter(ServiceRecord.end_time.is_(None))
        .order_by(ServiceRecord.start_time.desc())
        .first()
    )

    workstation = None
    initial_payload = None

    if active_session:
        # Get workstation
        workstation = (
            db.session.query(Workstation)
            .filter_by(workstation_id=active_session.workstation_id)
            .first()
        )

        # Fetch all SOP steps for the service
        db_checklist = (
            db.session.query(SOPStep, ServiceChecklist)
            .outerjoin(
                ServiceChecklist,
                (ServiceChecklist.step_id == SOPStep.step_id) &
                (ServiceChecklist.service_record_id == active_session.service_record_id)
            )
            .filter(SOPStep.service_id == active_session.service_id)
            .order_by(SOPStep.step_number)
            .all()
        )

        # Build checklist with correct checked status
        checklist = [
            {
                "step_id": step.step_id,
                "description": step.step_description,
                "checked": sc.is_checked if sc else False
            }
            for step, sc in db_checklist
        ]

        initial_payload = {
            "session_id": active_session.service_record_id,
            "service_record_id": active_session.service_record_id,
            "service": active_session.service_detected,
            "confidence": active_session.confidence or 0,
            "sop": checklist,
        }

    return render_template(
        "cs/dashboard.html",
        workstation=workstation,
        active_session=active_session,
        initial_payload=initial_payload
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

@socketio.on("session_end")
def handle_manual_end(data):
    rp_id = data.get("rp_id")
    reason = data.get("reason")
    sr_id = session_manager.end_session_by_rp(rp_id, reason=reason)
    
    if sr_id:
        sr = ServiceRecord.query.filter_by(service_record_id=sr_id).first()
        sr.is_normal_flow = 0
        db.session.commit()
        socketio.emit("session_ended", {"session_id": sr_id, "reason": reason})