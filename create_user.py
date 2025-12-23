from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    user = User(
        user_id="US0000",
        role_id="RL0000",
        name="Testing",
        email="testing@example.com",
        password=generate_password_hash("password"),
        is_active=1
    )

    db.session.add(user)
    db.session.commit()
    print("User created")