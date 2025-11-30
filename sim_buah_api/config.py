import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env hanya untuk local development
load_dotenv()

class Config:

    # --- SECURITY ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # --- DATABASE (RAILWAY MYSQL) ---
    # Hardcode URL langsung dari Railway
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:FASLvFHLsoARHzMYRuATCnFCvmwjkigR@switchyard.proxy.rlwy.net:33430/railway"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
