from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import timedelta

from .config import Config
from .database import db, bcrypt, jwt

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.url_map.strict_slashes = False

    # ==========================================================
    # ✅ FIX CORS FINAL UNTUK RAILWAY + VERCEL
    # ==========================================================
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True
    )

    # ✅ FIX PREFLIGHT OPTIONS (INI YANG MENGHENTIKAN ERROR CORS)
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
            return response, 200

    # ==========================================================
    # ✅ INIT EXTENSION
    # ==========================================================
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # ==========================================================
    # ✅ JWT CONFIG
    # ==========================================================
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)

    # ==========================================================
    # ✅ JWT ERROR HANDLER (ANTI CORS ERROR 401)
    # ==========================================================
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

    # ==========================================================
    # ✅ IMPORT MODEL (WAJIB UNTUK MIGRATION)
    # ==========================================================
    from . import models

    # ==========================================================
    # ✅ REGISTER BLUEPRINT
    # ==========================================================
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.master_routes import master_bp
    from .routes.transaksi_routes import transaksi_bp
    from .routes.laporan_routes import laporan_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.batch_stock_routes import batch_stock_bp
    from .routes.inventory_routes import inventory_bp
    from .routes.monitor_routes import monitor_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(master_bp, url_prefix="/api/master")
    app.register_blueprint(transaksi_bp, url_prefix="/api/transaksi")
    app.register_blueprint(laporan_bp, url_prefix="/api/laporan")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(batch_stock_bp, url_prefix="/api/batch-stock")
    app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
    app.register_blueprint(monitor_bp, url_prefix="/api/monitor")

    # ==========================================================
    # ✅ HEALTH CHECK
    # ==========================================================
    @app.route("/api/status", methods=["GET"])
    def get_status():
        return jsonify({
            "status": "ok",
            "service": "SIM Buah API is running"
        }), 200

    return app
