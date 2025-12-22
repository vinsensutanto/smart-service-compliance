class Config:
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://smart_user:smart_password@localhost/smart_service"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
