from flask_bcrypt import Bcrypt

# Inisialisasi tanpa app dulu (atau import dari app jika sudah di-init di __init__.py)
bcrypt = Bcrypt()

def hash_password(password):
    """Menghasilkan hash password menggunakan BCrypt"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def verify_password(stored_password, provided_password):
    """Memverifikasi password dengan format BCrypt ($2y$...)"""
    if not stored_password:
        return False
    return bcrypt.check_password_hash(stored_password, provided_password)