# /backend_flask/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import timedelta
from decimal import Decimal
# Pastikan Anda punya file-file ini
from sim_buah_api.config import Config 
from sim_buah_api.database import db, bcrypt, jwt 
from sim_buah_api.models import User, Role, Buah, Supplier, Pelanggan, LogAktivitas, BarangMasuk, BatchStok, BarangKeluar, DetailKeluar # Import semua models untuk setup

migrate = Migrate()

def create_app(config_class=Config):
    # Logika lengkap dari fungsi create_app() Anda
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    app.url_map.strict_slashes = False

    # FIX: Konfigurasi CORS Universal
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True, expose_headers=["Content-Disposition"]) 

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)

    # FIX KRITIS: JWT ERROR HANDLER (Menjamin CORS pada 401)
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        response = jsonify({'status': 'error', 'message': 'Otorisasi dibutuhkan. Token hilang atau sesi berakhir.'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        return response, 401
        
    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return unauthorized_callback(callback)
    
    # Import dan Register Blueprint (sesuaikan path impor)
    from sim_buah_api.routes.auth_routes import auth_bp
    from sim_buah_api.routes.admin_routes import admin_bp 
    # ... (Register semua blueprint lainnya di sini)

    # Contoh Registrasi Blueprint (asumsi)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # ... (Register semua Blueprint)

    @app.route('/api/status', methods=['GET'])
    def get_status():
        return jsonify({"status": "ok", "service": "SIM Buah API is running"}), 200
    
    return app

# ==============================================================
# LOGIC SETUP DATABASE (DIPERLUKAN UNTUK PENGEMBANGAN LOKAL)
# ==============================================================
# Objek 'app' dibuat di luar fungsi setup_database() agar bisa digunakan di dalamnya
app = create_app() 

def setup_database():
    """Fungsi untuk inisialisasi database dan seeding data awal."""
    with app.app_context():
        
        print("Mencoba membuat SEMUA tabel database (db.create_all())...")
        db.create_all() 
        print("Inisialisasi tabel selesai.")
        
        # Seeding Roles
        if Role.query.count() == 0:
            print("Seeding Roles...")
            roles = [
                Role(nama_role='Admin', deskripsi='Akses penuh ke semua modul dan konfigurasi.'),
                Role(nama_role='Manajer', deskripsi='Akses ke Laporan dan Transaksi.'),
                Role(nama_role='Petugas Gudang', deskripsi='Akses ke Transaksi Barang Masuk dan Keluar.')
            ]
            db.session.add_all(roles)
            db.session.commit()
            
        # Seeding User Admin Default
        admin_role = Role.query.filter_by(nama_role='Admin').first()
        if admin_role and not User.query.filter_by(username='admin').first():
            print("Menambahkan User Admin Default 'admin'...")
            admin = User(user_id=1, role_id=admin_role.role_id, username='admin', nama_lengkap='Super Admin Sistem')
            admin.set_password('12345678')
            db.session.add(admin)
            db.session.commit()

# ==============================================================
# START SERVER LOKAL (BLOK YANG ANDA MINTA)
# ==============================================================
if __name__ == '__main__':
    # Lakukan setup database dan seeding
    setup_database()
    
    # Jalankan server Flask
    print("\n--- Flask Server Running ---")
    print(f"Akses API Status: http://127.0.0.1:5000/api/status")
    print(f"Akses Login API: http://127.0.0.1:5000/api/auth/login")
    app.run(debug=True, host="0.0.0.0", port=5000)