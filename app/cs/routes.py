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
from app.services.stream_controller import publish_end_stream
from app.utils.decorators import role_required
from app.utils.scoring import calculate_session_score
from app.services.session_manager import attach_user_to_active_session
from flask_login import current_user

cs_bp = Blueprint("cs", __name__, template_folder="templates")

# =========================================
# CS DASHBOARD
# =========================================
@cs_bp.route("/dashboard")
@login_required
@role_required(["Customer Service"])
def dashboard():
    # 1. WAJIB: Inisialisasi semua variabel lokal di awal
    workstation = None
    active_session = None
    initial_payload = None
    
    # 2. Ambil PC_ID dari environment
    pc_id = os.getenv("PC_ID")
    
    # 3. Query (Jika PC_ID ada, isi variabel workstation)
    if pc_id:
        workstation = db.session.query(Workstation).filter_by(pc_id=pc_id).first()

    # 4. Sekarang aman, karena 'workstation' sudah dikenal (meskipun isinya None)
    if workstation:
        active_session = (
            db.session.query(ServiceRecord)
            .filter(
                ServiceRecord.workstation_id == workstation.workstation_id,
                ServiceRecord.end_time.is_(None)
            )
            .order_by(ServiceRecord.start_time.desc())
            .first()
        )
        
        # 5. Jika ada session, siapkan payload-nya
        if active_session:
            # Query checklist dari database
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
                "service": active_session.service_detected,
                "confidence": active_session.confidence or 0,
                "sop": checklist,
            }
            
    if active_session and not active_session.user_id:
        attach_user_to_active_session(
            rp_id=workstation.rpi_id,
            user_id=current_user.user_id
        )
    # 6. Kirim ke template
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
@role_required(["Customer Service"])
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
@role_required(["Customer Service"])
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
            # 🔹 GUNAKAN FUNGSI DARI UTILS
            # Jika utils Anda butuh object record utuh:
            record.session_score = calculate_session_score(record) 
            
            # Catatan: Jika fungsi di utils Anda hanya menerima (is_normal, reason), 
            # maka kodenya tetap record.session_score = calculate_session_score(record.is_normal_flow, record.reason)
            # tapi fungsi yang dipanggil sudah berasal dari utils (global).

            total_weighted_score += record.session_score

            if record.duration and record.duration > 0:
                valid_durations.append(record.duration)

        final_performance_score = round(total_weighted_score / total_sessions, 1)

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

@socketio.on("session_end")
def handle_manual_end(data):
    rp_id = data.get("rp_id")
    reason = data.get("reason")
    pc_id = os.getenv("PC_ID")

    ws = db.session.query(Workstation).filter_by(pc_id=pc_id, rpi_id=rp_id).first()
    if not ws:
        socketio.emit(
            "session_end_rejected",
            {"message": "Invalid RP for this PC", "rp_id": rp_id}
        )
        return

    # Get active session for this RP
    sr_id = session_manager.get_active_session_by_rp(rp_id)
    if not sr_id:
        socketio.emit(
            "session_end_rejected",
            {"message": "No active session", "rp_id": rp_id}
        )
        return

    # Assign current_user to session if missing
    session = db.session.query(ServiceRecord).filter_by(service_record_id=sr_id).first()
    if session and not session.user_id:
        session.user_id = current_user.user_id
        db.session.commit()

    # End session
    sr_id = session_manager.end_session_by_rp(
        rp_id=rp_id,
        reason=reason,
        manual_termination=True
    )

    if not sr_id:
        socketio.emit(
            "session_end_rejected",
            {"message": "Session cannot be ended", "rp_id": rp_id}
        )
        return

    publish_end_stream(sr_id)
    socketio.emit(
        "session_ended",
        {"session_id": sr_id, "reason": reason, "rp_id": rp_id}
    )