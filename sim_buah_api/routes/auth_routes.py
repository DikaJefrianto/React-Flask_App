# /backend_flask/sim_buah_api/routes/auth_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    unset_jwt_cookies,
    get_jwt
)
from ..database import db, bcrypt
from ..models import User, Role, LogAktivitas # <-- FIX 1: Import LogAktivitas
from datetime import timedelta, datetime

auth_bp = Blueprint('auth', __name__)

# ====================================================================
# A. LOGIN → Menghasilkan Access Token & Refresh Token (FIXED)
# ====================================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(msg="Username dan Password wajib diisi."), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify(msg="User tidak ditemukan."), 404

    if not user.is_active:
        return jsonify(msg="Akun tidak aktif."), 403

    if not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify(msg="Password salah."), 401

    # Ambil role (Admin, Manajer, Petugas Gudang)
    role = Role.query.get(user.role_id)

    # Payload untuk RBAC
    claims = {
        "username": user.username,
        "role": role.nama_role 
    }

    # TOKEN
    access_token = create_access_token(
        identity=str(user.user_id),
        additional_claims=claims,
        expires_delta=timedelta(minutes=30)
    )

    refresh_token = create_refresh_token(
        identity=str(user.user_id),
        expires_delta=timedelta(days=7)
    )

    # -------------------------------------------------------------
    # FIX 2: PENAMBAHAN LOG AKTIVITAS LOGIN
    # -------------------------------------------------------------
    try:
        log = LogAktivitas(
            user_id=user.user_id,
            jenis_aksi='LOGIN_SUCCESS',
            deskripsi=f'Pengguna {user.nama_lengkap} ({role.nama_role}) berhasil login.'
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # PENTING: Jika log gagal, jangan batalkan login.
        print(f"Error logging LOGIN activity: {e}")
        db.session.rollback()
    # -------------------------------------------------------------
    
    return jsonify({
        "message": "Login sukses",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_role": role.nama_role,
        "user_id": user.user_id
    }), 200


# ====================================================================
# B. REFRESH TOKEN → Menghasilkan Access Token baru
# ====================================================================
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    claims = get_jwt()

    # Buat ulang access token baru dengan claims lama (role, username)
    new_access = create_access_token(
        identity=user_id,
        additional_claims={
            "username": claims.get("username"),
            "role": claims.get("role"),
        },
        expires_delta=timedelta(minutes=30)
    )

    return jsonify({
        "access_token": new_access
    }), 200


# ====================================================================
# C. Profile User
# ====================================================================
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify(msg="User tidak ditemukan."), 404

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "nama_lengkap": user.nama_lengkap,
        "role": user.role.nama_role
    }), 200


# ====================================================================
# D. LOGOUT — Menghapus cookies JWT (jika pakai cookies)
# ====================================================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    # Catatan: Jika token disimpan di localStorage (seperti di frontend Anda),
    # penghapusan di sisi klien (frontend) lebih utama daripada unset_jwt_cookies.
    response = jsonify({'msg': 'Logout berhasil'})
    unset_jwt_cookies(response)
    return response, 200