import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import func
from datetime import datetime, timezone
from app.extensions import db
from app.models import User, ServiceRecord, Workstation, SOPService
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

@spv_bp.route("/performance-analytics")
def performance_analytics():
    # 1. Query Statistik Utama
    total_sessions = ServiceRecord.query.count()
    # Jika tabel masih kosong, set default agar tidak division by zero
    if total_sessions == 0:
        return render_template("spv/performance-analytics.html", 
                               total_sessions=0, compliance_rate=0,
                               dates="[]", totals="[]", compliances="[]", leaderboard=[])

    compliance_count = ServiceRecord.query.filter_by(is_normal_flow=1).count()
    compliance_rate = round((compliance_count / total_sessions * 100), 1)
    
    # 2. Data untuk Line Chart (Tren 7 Hari Terakhir)
    trend_data = db.session.query(
        func.date(ServiceRecord.start_time).label('date'),
        func.count(ServiceRecord.service_record_id).label('total'),
        func.sum(ServiceRecord.is_normal_flow).label('compliant')
    ).group_by(func.date(ServiceRecord.start_time)).order_by('date').all()

    dates = [d.date.strftime('%d %b') for d in trend_data]
    totals = [int(d.total) for d in trend_data]
    compliances = [int(d.compliant if d.compliant else 0) for d in trend_data]

    # 3. Data untuk Leaderboard Staff 
    raw_leaderboard = db.session.query(
        User.name,
        ServiceRecord.is_normal_flow,
        ServiceRecord.reason,
        User.user_id
    ).join(ServiceRecord, User.user_id == ServiceRecord.user_id).all()

    # Proses perhitungan manual di Python agar lebih fleksibel
    processed_stats = {}
    for name, is_normal, reason, uid in raw_leaderboard:
        score = calculate_session_score(is_normal, reason)
        if name not in processed_stats:
            processed_stats[name] = {"total_score": 0, "count": 0}
        processed_stats[name]["total_score"] += score
        processed_stats[name]["count"] += 1

    # Format untuk dikirim ke template
    final_leaderboard = []
    for name, data in processed_stats.items():
        avg_score = round(data["total_score"] / data["count"], 1)
        final_leaderboard.append({
            "name": name,
            "avg_score": avg_score,
            "count": data["count"]
        })

    # Urutkan berdasarkan skor tertinggi
    final_leaderboard = sorted(final_leaderboard, key=lambda x: x['avg_score'], reverse=True)

    return render_template("spv/performance-analytics.html", 
                           total_sessions=total_sessions,
                           compliance_rate=compliance_rate,
                           dates=json.dumps(dates),
                           totals=json.dumps(totals),
                           compliances=json.dumps(compliances),
                           leaderboard=final_leaderboard)

def calculate_session_score(is_normal, reason):
    if is_normal == 1:
        return 100
    
    # Mapping bobot berdasarkan alasan bypass
    weights = {
        "System Error / AI not responding": 90,
        "Customer cancelled or left early": 80,
        "Staff forgot to finish session": 40,
        "other": 60
    }
    return weights.get(reason, 60) # Default 60 jika alasan tidak dikenal