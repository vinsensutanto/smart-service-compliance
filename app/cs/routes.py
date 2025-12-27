# app/cs/routes.py
import os
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.models.workstation import Workstation
from app.extensions import db
from app.services.session_manager import active_sessions
from app.models.sop_service import SOPService 
from app.models.sop_step import SOPStep    
from app.models.service_record import ServiceRecord   

# template_folder='templates' merujuk ke folder 'templates' di dalam folder 'cs'
cs_bp = Blueprint('cs', __name__, template_folder='templates')

@cs_bp.route('/dashboard')
@login_required
def dashboard():
# 1. Ambil ID dari .env
    ws_id = os.getenv("WORKSTATION_ID") 
    
    # 2. Query ke database mencari WS0002
    ws_info = Workstation.query.filter_by(workstation_id=ws_id).first()
    
    # 3. (Optional) Set agar di DB statusnya jadi aktif (1)
    if ws_info:
        ws_info.is_active = True
        db.session.commit()

    active_session = next((s for s in active_sessions.values() if s.workstation_id == "WS0001"), None)
    
    return render_template(
        "cs/dashboard.html",
        workstation=ws_info,
        active_session=active_session  # Kirim data sesi yang sedang jalan ke HTML
    )

@cs_bp.route('/service-guidelines')
@login_required
def service_guidelines():
    # 1. Ambil semua data layanan (SV0001, SV0002, dll)
    services = db.session.query(SOPService).all()
    
    # 2. Ambil semua data langkah-langkah (ST0001, ST0002, dll)
    # Kita ambil semua sekaligus karena ini halaman statis
    steps = db.session.query(SOPStep).order_by(SOPStep.step_number.asc()).all()
    
    # 3. Kirim ke file HTML kamu
    return render_template('cs/service-guidelines.html', 
                           services=services, 
                           steps=steps)

@cs_bp.route('/my-history')
@login_required
def my_history():
    # Query data berdasarkan user_id yang sedang login
    history = ServiceRecord.query.filter_by(user_id=current_user.user_id)\
              .order_by(ServiceRecord.start_time.desc()).all()
    return render_template('cs/my-history.html', history=history)

