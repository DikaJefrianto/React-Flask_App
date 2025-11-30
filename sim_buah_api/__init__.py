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

    # ============================
    # ✅ CORS FIX FINAL (VERCEL → RAILWAY)
    # ============================
    CORS(app,
         resources={r"/api/*": {
             "origins": [
                 "https://react-frontend-dusky-rho.vercel.app"
             ],
             "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }},
         expose_headers=["Content-Disposition"]
    )

    db.init_app(app)
    jwt.init_app(app) 
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)

    # =========================================
    # ✅ JWT ERROR HANDLER (ANTI ERROR CORS 401)
    # =========================================
    
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        response = jsonify({
            'status': 'error', 
            'message': 'Otorisasi dibutuhkan. Token hilang atau sesi berakhir.'
        })
        return response, 401 
        
    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return unauthorized_callback(callback)

    # ============================
    # ✅ REGISTER BLUEPRINT
    # ============================
    
    from . import models
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp 
    from .routes.master_routes import master_bp 
    from .routes.transaksi_routes import transaksi_bp
    from .routes.laporan_routes import laporan_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.batch_stock_routes import batch_stock_bp
    from .routes.inventory_routes import inventory_bp
    from .routes.monitor_routes import monitor_bp

    app.register_blueprint(batch_stock_bp, url_prefix='/api/batch-stock')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(master_bp, url_prefix='/api/master')
    app.register_blueprint(transaksi_bp, url_prefix='/api/transaksi')
    app.register_blueprint(laporan_bp, url_prefix='/api/laporan')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')

    @app.route('/api/status', methods=['GET'])
    def get_status():
        return jsonify({
            "status": "ok",
            "service": "SIM Buah API is running"
        }), 200
    
    return app
