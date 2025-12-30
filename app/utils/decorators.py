from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from app.models import Role

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth_web.login'))
            
            # Ambil nama role user saat ini
            role = Role.query.get(current_user.role_id)
            if not role or role.role_name not in allowed_roles:
                # Jika role tidak diizinkan, kasih error 403 atau lempar ke dashboard aslinya
                flash("You do not have permission to access this page.", "danger")
                if role and role.role_name == "Supervisor":
                    return redirect("/spv/dashboard")
                else:
                    return redirect("/cs/dashboard")
            return f(*args, **kwargs)
        return decorated_function
    return decorator