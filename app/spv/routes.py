import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy import func
from datetime import datetime, timezone
from app.extensions import db
from app.models import User, ServiceRecord, Workstation, SOPService
from app.utils.decorators import role_required
from app.utils.scoring import calculate_session_score

spv_bp = Blueprint(
    "spv",
    __name__,
    template_folder="templates"
)


@spv_bp.route("/dashboard")
@login_required
@role_required(["Supervisor"])
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
@login_required
@role_required(["Supervisor"])
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
@login_required
@role_required(["Supervisor"])
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

@spv_bp.route("/performance-analytics")
@login_required
@role_required(["Supervisor"])
def performance_analytics():
    # 1. Query hanya sesi yang sudah SELESAI (Sesuai Logika CS)
    finished_query = ServiceRecord.query.filter(ServiceRecord.end_time.isnot(None))
    total_sessions = finished_query.count()
    
    if total_sessions == 0:
        return render_template("spv/performance-analytics.html", 
                               total_sessions=0, compliance_rate=0,
                               dates="[]", totals="[]", compliances="[]", leaderboard=[])

    # 2. Hitung Average Performance Score (Weighted)
    all_sessions = finished_query.all()
    total_weighted_sum = sum(calculate_session_score(s.is_normal_flow, s.reason) for s in all_sessions)
    compliance_rate = round(total_weighted_sum / total_sessions, 1)
    
    # 3. Trend Data untuk Chart (Hanya Sesi Selesai)
    trend_data = db.session.query(
        func.date(ServiceRecord.start_time).label('date'),
        func.count(ServiceRecord.service_record_id).label('total'),
        func.sum(ServiceRecord.is_normal_flow).label('compliant')
    ).filter(ServiceRecord.end_time.isnot(None))\
     .group_by(func.date(ServiceRecord.start_time))\
     .order_by('date').all()

    dates = [d.date.strftime('%d %b') for d in trend_data]
    totals = [int(d.total) for d in trend_data]
    compliances = [int(d.compliant if d.compliant else 0) for d in trend_data]

    # 4. Leaderboard Staf (Weighted Score)
    raw_leaderboard = db.session.query(
        User.user_id, User.name, ServiceRecord.is_normal_flow, ServiceRecord.reason
    ).join(ServiceRecord, User.user_id == ServiceRecord.user_id)\
     .filter(ServiceRecord.end_time.isnot(None)).all()

    processed_stats = {}
    for uid, name, is_normal, reason in raw_leaderboard:
        score = calculate_session_score(is_normal, reason)
        if uid not in processed_stats:
            processed_stats[uid] = {"name": name, "total_score": 0, "count": 0}
        processed_stats[uid]["total_score"] += score
        processed_stats[uid]["count"] += 1

    final_leaderboard = []
    for uid, data in processed_stats.items():
        final_leaderboard.append({
            "user_id": uid,
            "name": data["name"],
            "avg_score": round(data["total_score"] / data["count"], 1),
            "count": data["count"]
        })

    final_leaderboard = sorted(final_leaderboard, key=lambda x: x['avg_score'], reverse=True)[:5]

    return render_template("spv/performance-analytics.html", 
                           total_sessions=total_sessions,
                           compliance_rate=compliance_rate,
                           dates=json.dumps(dates),
                           totals=json.dumps(totals),
                           compliances=json.dumps(compliances),
                           leaderboard=final_leaderboard)

# =========================================
# STAFF DETAIL VIEW (SINKRON DENGAN CS)
# =========================================
@spv_bp.route("/performance/staff/<user_id>")
@login_required
@role_required(["Supervisor"])
def staff_performance_detail(user_id):
    staff = User.query.get_or_404(user_id)
    
    # Filter: Hanya sesi yang SUDAH SELESAI
    sessions = ServiceRecord.query.filter(
        ServiceRecord.user_id == user_id,
        ServiceRecord.end_time.isnot(None)
    ).order_by(ServiceRecord.start_time.desc()).all()
    
    total = len(sessions)
    avg_performance = 0
    avg_dur = 0
    
    if total > 0:
        total_weighted_score = 0
        valid_durations = []
        
        for s in sessions:
            # Hitung skor tiap sesi (Sesuai CS: 100, 90, 80, 40, 60)
            s.calculated_score = calculate_session_score(s.is_normal_flow, s.reason)
            total_weighted_score += s.calculated_score
            
            if s.duration and s.duration > 0:
                valid_durations.append(s.duration)
        
        # Rata-rata Skor (Weighted)
        avg_performance = round(total_weighted_score / total, 1)
        
        if valid_durations:
            avg_dur = int(sum(valid_durations) / len(valid_durations))

    return render_template(
        "spv/staff-detail.html", 
        staff=staff, 
        sessions=sessions, 
        total=total, 
        avg_performance=avg_performance,
        avg_dur=avg_dur
    )