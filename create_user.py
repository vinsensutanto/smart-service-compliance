from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    user = User(
        user_id="CS001",
        role_id="RL001",
        name="Customer Service 1",
        email="cs1@bank.com",
        password_hash=generate_password_hash("password123"),
        is_active=True
    )

    db.session.add(user)
    db.session.commit()
    print("User created")
