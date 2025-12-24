from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    if not User.query.filter_by(user_id="US0001").first():
        user = User(
            user_id="US0001",
            role_id="RL0001",
            name="Unknown User",
            email="unknown@example.com",
            password=generate_password_hash("password123"),
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        print("User 'US0001' created")
    else:
        print("User 'US0001' already exists")
