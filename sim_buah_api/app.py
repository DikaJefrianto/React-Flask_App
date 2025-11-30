# /backend_flask/app.py
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from datetime import timedelta

# --- 1. INISIALISASI APLIKASI DAN KONFIGURASI ---

# Inisialisasi Objek Flask
app = Flask(__name__)

# Memuat konfigurasi dari class Config (mengambil nilai dari .env)
app.config.from_object(Config)

# --- 2. INISIALISASI EXTENSIONS ---

# Inisialisasi SQLAlchemy ORM (Database connection)
db = SQLAlchemy(app)

# Inisialisasi CORS (Mengizinkan koneksi dari frontend React/Express)
CORS(app, supports_credentials=True) 

# Inisialisasi Flask-JWT-Extended (Untuk Token Authentication)
jwt = JWTManager(app)

# Tambahan: Set waktu kadaluarsa token (NFR-SE01: 15 menit)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)

# --- 3. IMPOR MODEL DAN BLUEPRINTS (ROUTES) ---

# Impor SEMUA Model Database (WAJIB agar db.create_all() mengenali semua tabel)
from .models import (
    Role, User, Buah, Supplier, Pelanggan, 
    BarangMasuk, BatchStok, BarangKeluar, DetailKeluar, LogAktivitas
)

# Impor dan Daftarkan Blueprints (API Endpoints)
from .routes.auth_routes import auth_bp
from .routes.admin_routes import admin_bp # Modul Pengelolaan User
# TO DO: Buat dan impor master_routes dan transaksi_routes di langkah selanjutnya
# from .routes.master_routes import master_bp
# from .routes.transaksi_routes import transaksi_bp

# Daftarkan Blueprint di Aplikasi Flask
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin') # Pengelolaan User oleh Admin
# app.register_blueprint(master_bp, url_prefix='/api/v1/master')
# app.register_blueprint(transaksi_routes, url_prefix='/api/v1/transaksi')


# --- 4. DEFAULT ROUTE (Health Check) ---
@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint sederhana untuk cek kesehatan API."""
    return jsonify({"status": "ok", "service": "SIM Buah API is running"}), 200

# --- 5. SETUP DAN JALANKAN APLIKASI ---

def setup_app():
    """Fungsi untuk inisialisasi database dan seeding data awal."""
    with app.app_context():
        
        # 1. Buat Tabel Database (jika belum ada di PostgreSQL)
        print("Mencoba membuat SEMUA tabel database (db.create_all())...")
        db.create_all() 
        print("Inisialisasi tabel selesai.")
        
        # 2. Seeding Data Awal (Roles)
        if Role.query.count() == 0:
            print("Seeding Roles...")
            roles = [
                Role(nama_role='Admin', deskripsi='Akses penuh ke semua modul dan konfigurasi.'),
                Role(nama_role='Manajer', deskripsi='Akses ke Laporan dan Transaksi (sesuai NFR-SE03).'),
                Role(nama_role='Petugas Gudang', deskripsi='Akses ke Transaksi Barang Masuk dan Keluar.')
            ]
            db.session.add_all(roles)
            db.session.commit()
            print("3 Roles berhasil ditambahkan.")
            
        # 3. Seeding User Admin Default
        admin_role = Role.query.filter_by(nama_role='Admin').first()
        if admin_role and not User.query.filter_by(username='admin').first():
             print("Menambahkan User Admin Default 'root'...")
             admin = User(user_id=1, role_id=admin_role.role_id, username='admin', nama_lengkap='Super Admin Sistem')
             admin.set_password('12345678') # Sandi akan di-hash
             db.session.add(admin)
             db.session.commit()
             print(f"User '{admin.username}' berhasil ditambahkan.")

        # 4. Seeding Data Master Buah Default (Contoh)
        if Buah.query.count() == 0:
            print("Menambahkan data buah default...")
            buah_1 = Buah(nama_buah='Apel Fuji', satuan='kg', stok_total=0, umur_simpan_hari=30)
            buah_2 = Buah(nama_buah='Mangga Gedong', satuan='kg', stok_total=0, umur_simpan_hari=15)
            db.session.add_all([buah_1, buah_2])
            db.session.commit()
            print("Data Buah default berhasil ditambahkan.")


if __name__ == '__main__':
    # Lakukan setup database dan seeding
    setup_app()
    
    # Jalankan server Flask
    print("\n--- Flask Server Running ---")
    print(f"Akses API Status: http://127.0.0.1:5000/api/status")
    print(f"Akses Login API: http://127.0.0.1:5000/api/auth/login")
    app.run(debug=True, port=5000)