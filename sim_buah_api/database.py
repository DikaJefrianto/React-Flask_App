# /backend_flask/sim_buah_api/database.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# Objek Singleton: Dibuat di sini untuk diimpor oleh models dan routes
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()