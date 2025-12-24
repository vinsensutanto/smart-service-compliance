from app import create_app
from app.extensions import db
from app.models.workstation import Workstation

app = create_app()

with app.app_context():
    workstations_to_create = [
        {
            "workstation_id": "WS0001",  # must start with WS
            "pc_id": "PC0001",            # matches chk_pc_id
            "rpi_id": "RP0001",           # matches chk_rpi_id
            "location": "Front Desk",
            "is_active": True
        },
        {
            "workstation_id": "WS0002",
            "pc_id": "PC0002",
            "rpi_id": "RP0002",
            "location": "Back Office",
            "is_active": False
        }
    ]

    for ws_data in workstations_to_create:
        existing = Workstation.query.filter_by(workstation_id=ws_data["workstation_id"]).first()
        if not existing:
            ws = Workstation(**ws_data)
            db.session.add(ws)
            print(f"Workstation '{ws_data['workstation_id']}' created")
        else:
            print(f"Workstation '{ws_data['workstation_id']}' already exists")

    db.session.commit()

from app import create_app
from app.extensions import db
from app.models.workstation import Workstation

app = create_app()

with app.app_context():
    workstations_to_create = [
        {
            "workstation_id": "WS0001",  # must start with WS
            "pc_id": "PC0001",            # matches chk_pc_id
            "rpi_id": "RP0001",           # matches chk_rpi_id
            "location": "Front Desk",
            "is_active": True
        },
        {
            "workstation_id": "WS0002",
            "pc_id": "PC0002",
            "rpi_id": "RP0002",
            "location": "Back Office",
            "is_active": False
        }
    ]

    for ws_data in workstations_to_create:
        existing = Workstation.query.filter_by(workstation_id=ws_data["workstation_id"]).first()
        if not existing:
            ws = Workstation(**ws_data)
            db.session.add(ws)
            print(f"Workstation '{ws_data['workstation_id']}' created")
        else:
            print(f"Workstation '{ws_data['workstation_id']}' already exists")

    db.session.commit()
