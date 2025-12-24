from app import create_app
from app.extensions import db
from app.models.role import Role

app = create_app()

with app.app_context():
    roles_to_create = [
        {"role_id": "RL0001", "role_name": "CS"},
        {"role_id": "RL0002", "role_name": "Admin"},
    ]

    for r in roles_to_create:
        existing = Role.query.filter_by(role_id=r["role_id"]).first()
        if not existing:
            role = Role(**r)
            db.session.add(role)
            print(f"Role '{r['role_id']}' created")
        else:
            print(f"Role '{r['role_id']}' already exists")
    
    db.session.commit()
