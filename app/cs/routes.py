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

    total_sessions = len(history)
    final_performance_score = 0
    avg_duration = 0
    fastest_service = None

    if total_sessions > 0:
        total_weighted_score = 0
        valid_durations = []

        for record in history:
            # 🔹 HITUNG SCORE PER SESSION
            record.session_score = calculate_session_score(
                record.is_normal_flow,
                record.reason
            )

            total_weighted_score += record.session_score

            if record.duration and record.duration > 0:
                valid_durations.append(record.duration)

        final_performance_score = round(
            total_weighted_score / total_sessions, 1
        )

        if valid_durations:
            avg_duration = int(sum(valid_durations) / len(valid_durations))

            fastest_service = min(
                [r for r in history if r.duration and r.duration > 0],
                key=lambda x: x.duration,
                default=None
            )

    return render_template(
        "cs/my-history.html",
        history=history,
        total_sessions=total_sessions,
        final_performance_score=final_performance_score,
        avg_duration=avg_duration,
        fastest_service=fastest_service
    )

def calculate_session_score(is_normal, reason):
    if is_normal == 1:
        return 100

    weights = {
        "System Error / AI not responding": 90,
        "Customer cancelled or left early": 80,
        "Staff forgot to finish session": 40,
    }
    return weights.get(reason, 60)


@socketio.on("session_end")
def handle_manual_end(data):
    rp_id = data.get("rp_id")
    reason = data.get("reason")

    sr_id = session_manager.end_session_by_rp(
        rp_id=rp_id,
        reason=reason
    )

    if not sr_id:
        socketio.emit(
            "session_end_rejected",
            {
                "message": "Session cannot be ended"
            }
        )
        return

    socketio.emit(
        "session_ended",
        {
            "session_id": sr_id,
            "reason": reason
        }
    )