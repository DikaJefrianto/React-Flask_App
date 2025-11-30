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

    # --- DATABASE (WAJIB DARI RAILWAY SAAT PRODUCTION) ---
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "DATABASE_URL tidak ditemukan! "
            "Pastikan sudah disetel di Railway Variables."
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
