from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import timedelta

# ==============================
# ✅ IMPORT CONFIG & EXTENSION
# ==============================
from sim_buah_api.config import Config
from sim_buah_api.database import db, bcrypt, jwt
from sim_buah_api.models import User, Role, Buah, Supplier, Pelanggan, LogAktivitas

# ==============================
# ✅ INISIALISASI APP
# ==============================
app = Flask(__name__)
app.config.from_object(Config)
app.url_map.strict_slashes = False

# ==============================
# ✅ CORS GLOBAL
# ==============================
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True
)

# ==============================
# ✅ FIX PREFLIGHT OPTIONS
# ==============================
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
        return response, 200

# ==============================
# ✅ INIT EXTENSIONS
# ==============================
db.init_app(app)
jwt.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

# ==============================
# ✅ JWT CONFIG
# ==============================
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)

# ==============================
# ✅ JWT ERROR HANDLER
# ==============================
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    response = jsonify({
        "status": "error",
        "message": "Token tidak ditemukan atau tidak valid"
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return unauthorized_callback(callback)

# ==============================
# ✅ IMPORT & REGISTER BLUEPRINT
# ==============================
from sim_buah_api.routes.auth_routes import auth_bp
from sim_buah_api.routes.admin_routes import admin_bp
from sim_buah_api.routes.master_routes import master_bp
from sim_buah_api.routes.transaksi_routes import transaksi_bp
from sim_buah_api.routes.laporan_routes import laporan_bp
from sim_buah_api.routes.dashboard_routes import dashboard_bp
from sim_buah_api.routes.batch_stock_routes import batch_stock_bp
from sim_buah_api.routes.inventory_routes import inventory_bp
from sim_buah_api.routes.monitor_routes import monitor_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(master_bp, url_prefix="/api/master")
app.register_blueprint(transaksi_bp, url_prefix="/api/transaksi")
app.register_blueprint(laporan_bp, url_prefix="/api/laporan")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(batch_stock_bp, url_prefix="/api/batch-stock")
app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
app.register_blueprint(monitor_bp, url_prefix="/api/monitor")

# ==============================
# ✅ HEALTH CHECK
# ==============================
@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "status": "ok",
        "service": "SIM Buah API is running"
    }), 200

# ==============================
# ✅ SETUP DATABASE & SEEDING
# ==============================
def setup_database():
    """Inisialisasi tabel + seeding roles + admin default"""
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
            print("3 Roles berhasil ditambahkan.")

        # Seeding Admin Default
        admin_role = Role.query.filter_by(nama_role='Admin').first()
        if admin_role and not User.query.filter_by(username='admin').first():
            print("Menambahkan User Admin Default 'admin'...")
            admin = User(role_id=admin_role.role_id, username='admin', nama_lengkap='Super Admin Sistem')
            admin.set_password('12345678')
            db.session.add(admin)
            db.session.commit()
            print(f"User '{admin.username}' berhasil ditambahkan (Sandi: 12345678).")

# ==============================
# ✅ LOCAL RUN
# ==============================
if __name__ == "__main__":
    # Setup database otomatis saat server dijalankan
    setup_database()

    print("\n--- Flask Server Running ---")
    print(f"Akses API Status: http://127.0.0.1:5000/api/status")
    print(f"Akses Login API: http://127.0.0.1:5000/api/auth/login")
    app.run(debug=True, host="0.0.0.0", port=5000)
