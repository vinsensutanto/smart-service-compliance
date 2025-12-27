# app/cs/routes.py
import os
from flask import Blueprint, render_template
from flask_login import login_required
from app.models.workstation import Workstation
from app.extensions import db
from app.services.session_manager import active_sessions

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
    # Ini akan mencari file: app/cs/templates/cs/service_guidelines.html
    return render_template('cs/service-guidelines.html')

@cs_bp.route('/my-history')
@login_required
def my_history():
    return render_template('cs/my-history.html')

