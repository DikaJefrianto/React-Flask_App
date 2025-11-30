from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import timedelta

# ==============================
# ✅ IMPORT CONFIG & EXTENSION
# ==============================
from sim_buah_api.config import Config
from sim_buah_api.database import db, bcrypt, jwt

# ==============================
# ✅ INISIALISASI APP
# ==============================
app = Flask(__name__)
app.config.from_object(Config)

app.url_map.strict_slashes = False

# ==============================
# ✅ CORS GLOBAL (RAILWAY + VERCEL AMAN)
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
# ✅ JWT ERROR HANDLER (ANTI CORS ERROR)
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
# ✅ IMPORT MODEL (WAJIB UNTUK MIGRATION)
# ==============================
from sim_buah_api import models

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
# ✅ LOCAL RUN (OPTIONAL)
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
