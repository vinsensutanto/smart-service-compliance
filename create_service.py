# scripts/create_service.py
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import role, user, workstation, service_record

app = create_app()

with app.app_context():
    # --- Role ---
    if not role.Role.query.filter_by(role_id="RL0001").first():
        r = role.Role(role_id="RL0001", role_name="Admin")
        db.session.add(r)

    # --- User ---
    if not user.User.query.filter_by(user_id="US0001").first():
        u = user.User(
            user_id="US0001",
            role_id="RL0001",
            name="Test User",
            email="test@example.com",
            password="password",  # consider hashing for real app
            is_active=True
        )
        db.session.add(u)

    # --- Workstation ---
    if not workstation.Workstation.query.filter_by(workstation_id="WS0001").first():
        w = workstation.Workstation(
            workstation_id="WS0001",
            pc_id="PC0001",
            rpi_id="RP0001",
            location="Lab",
            is_active=True
        )
        db.session.add(w)

    # --- Service Records ---
    if not service_record.ServiceRecord.query.filter_by(service_record_id="SR0001").first():
        sr = service_record.ServiceRecord(
            service_record_id="SR0001",
            workstation_id="WS0001",
            user_id="US0001",
            service_detected="Test Service",
            confidence=1.0,
            start_time=datetime.utcnow()
        )
        db.session.add(sr)

    db.session.commit()
    print("Parent rows created successfully!")
