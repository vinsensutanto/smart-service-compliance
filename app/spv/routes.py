from flask import Blueprint, render_template
from app.extensions import db
from app.models.user import User
from app.models.workstation import Workstation
from app.models.service_record import ServiceRecord
from sqlalchemy import func
from datetime import datetime

spv_bp = Blueprint('spv', __name__, template_folder='templates')

@spv_bp.route('/dashboard')
def dashboard():
    # 1. Ambil tanggal hari ini (UTC/Lokal sesuai server)
    today = datetime.utcnow().date()
    
    # 2. Hitung Total Sesi Hari Ini
    total_sessions = db.session.query(ServiceRecord).filter(
        func.date(ServiceRecord.start_time) == today
    ).count()
    
    # 3. Ambil Status Meja (Workstation) & User yang sedang duduk
    # Kita join ke User untuk melihat siapa yang online
    stations = db.session.query(Workstation, User).\
        outerjoin(User, Workstation.workstation_id == User.user_id).all()
    
    # 4. Ambil Alert Override (is_normal_flow = 0)
    # Kita butuh data ServiceRecord untuk 'reason' dan User untuk 'name'
    alerts = db.session.query(ServiceRecord, User).\
        join(User, ServiceRecord.user_id == User.user_id).\
        filter(
            func.date(ServiceRecord.start_time) == today,
            ServiceRecord.is_normal_flow == 0
        ).order_by(ServiceRecord.start_time.desc()).all()

    return render_template('spv/dashboard.html', 
                           total_sessions=total_sessions,
                           stations=stations,
                           alerts=alerts)