# # /backend_flask/config.py
# import os
# from dotenv import load_dotenv

# from datetime import timedelta

# # Konfigurasi Access Token (pendek) dan Refresh Token (panjang)

# # Memastikan semua variabel di file .env dimuat
# load_dotenv() 

# class Config:
#     # --- Pengaturan Kunci Rahasia ---
#     SECRET_KEY = os.environ.get('SECRET_KEY') 
#     JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') 
#     JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1) 
#     JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
#     # --- Database PostgreSQL Configuration ---
#     DB_USER = os.environ.get('DATABASE_USER')
#     DB_PASS = os.environ.get('DATABASE_PASS')
#     DB_HOST = os.environ.get('DATABASE_HOST')
#     DB_PORT = os.environ.get('DATABASE_PORT', 5432)
#     DB_NAME = os.environ.get('DATABASE_NAME')
    
#     # Konstruksi URI Koneksi SQLAlchemy
#     # Format: postgresql://user:password@host:port/database_name
#     SQLALCHEMY_DATABASE_URI ="mysql://root:@localhost/sim_buah_db"
    
#     SQLALCHEMY_TRACK_MODIFICATIONS = False

# /backend_flask/config.py
import os
from dotenv import load_dotenv
from datetime import timedelta

# Memastikan semua variabel di file .env dimuat
load_dotenv() 

class Config:
    # ... (Pengaturan Kunci Rahasia JWT, dsb. tetap sama)

    # --- PENGATURAN DATABASE ---
    
    # Ambil variabel lingkungan dari Railway (seperti POSTGRES_URL atau DATABASE_URL)
    # Jika variabel ini ada (di Production), maka akan digunakan.
    # Jika tidak ada (di Development lokal), maka akan kembali ke default.
    
    # 1. Gunakan variabel lingkungan standar (yang disuntikkan oleh Render/Railway)
    #    Jika Anda menggunakan PyMySQL/MySQL, formatnya: mysql+pymysql://...
    #    Jika Anda menggunakan PostgreSQL (lebih umum di Railway), gunakan format pgsql://...
    
    # FIX KRITIS: Prioritaskan DATABASE_URL yang disetel di Railway, 
    #             sebelum kembali ke hardcoded local (jika ada).
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or "mysql+pymysql://root:@localhost/sim_buah_db"
    
    # Jika Anda menggunakan driver mysqlclient, pastikan PyMySQL diinstal:
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "mysql://root:@localhost/sim_buah_db"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False