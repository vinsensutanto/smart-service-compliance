from app import create_app
from app.extensions import db
from app.models.role import Role

app = create_app()

with app.app_context():
    role = Role(
        role_id="RL001",
        role_name="CS"
    )
    db.session.add(role)
    db.session.commit()
    print("Role created")
