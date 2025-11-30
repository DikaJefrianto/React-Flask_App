# /backend_flask/routes/admin_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..database import db
from ..models import User, Role # Impor model
from functools import wraps
# FIX KRITIS: Import record_log dari lokasi baru
from ..utils.log_helper import record_log 

admin_bp = Blueprint('admin', __name__)


# --- 1. HELPER: DECORATOR UNTUK RBAC (ROLE CHECKING) ---
def admin_required():
    """Decorator kustom untuk membatasi akses hanya untuk user dengan Role 'Admin'."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role != 'Admin':
                return jsonify(msg="Akses Ditolak: Hanya Admin yang dapat mengakses modul ini."), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# --- 2. API ENDPOINTS UNTUK USER MANAGEMENT (CRUD) ---

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_users():
    """[READ] Mengambil daftar semua pengguna beserta Role mereka."""
    try:
        users = db.session.query(User, Role).join(Role).all()
        result = []
        for user, role in users:
            result.append({
                'user_id': user.user_id,
                'username': user.username,
                'nama_lengkap': user.nama_lengkap,
                'role': role.nama_role,
                'is_active': user.is_active
            })
        
        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error saat mengambil data user: {str(e)}'}), 500


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
def create_user():
    """[CREATE] Membuat pengguna baru (Manajer/Petugas Gudang)."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password', '12345678')
    nama_lengkap = data.get('nama_lengkap')
    role_name = data.get('role')

    # ... (Validasi input dan role)
    if not username or not role_name:
        return jsonify({'message': 'Username dan Role wajib diisi.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username sudah terdaftar.'}), 409
    role = Role.query.filter_by(nama_role=role_name).first()
    if not role:
        return jsonify({'message': f'Role "{role_name}" tidak valid.'}), 400

    try:
        new_user = User(
            username=username,
            nama_lengkap=nama_lengkap,
            role_id=role.role_id,
            is_active=True
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit() # Commit transaksi utama
        
        # --- FIX 2: Panggil record_log setelah Commit sukses ---
        record_log(
            action_type='USER_CREATE',
            description=f'Menambahkan user: {new_user.username} ({role_name})'
        )
        
        return jsonify({'message': f'User {username} ({role_name}) berhasil dibuat.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error saat membuat user: {str(e)}'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_user(user_id):
    """[UPDATE] Memperbarui detail pengguna."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Inisialisasi deskripsi log
    log_desc = f'Memperbarui user ID {user_id}: '
    is_updated = False
    
    try:
        # --- Update Username ---
        if 'username' in data and user.username != data['username']:
            new_username = data['username']
            existing = User.query.filter(User.username == new_username, User.user_id != user_id).first()
            if existing:
                return jsonify({'message': 'Username sudah digunakan user lain.'}), 409
            user.username = new_username
            log_desc += 'Username, '
            is_updated = True

        # --- Update Nama Lengkap ---
        if 'nama_lengkap' in data and user.nama_lengkap != data['nama_lengkap']:
            user.nama_lengkap = data['nama_lengkap']
            log_desc += 'Nama Lengkap, '
            is_updated = True

        # --- Update Role ---
        if 'role' in data and user.role.nama_role != data['role']:
            role = Role.query.filter_by(nama_role=data['role']).first()
            if not role:
                return jsonify({'message': f'Role "{data["role"]}" tidak valid.'}), 400
            user.role_id = role.role_id
            log_desc += f'Role ({role.nama_role}), '
            is_updated = True

        # --- Update Status (Active/Inactive) ---
        if 'is_active' in data and bool(user.is_active) != bool(data['is_active']):
            user.is_active = data['is_active']
            log_desc += f'Status Aktif ({user.is_active}), '
            is_updated = True

        # --- Update Password bila diisi ---
        if 'password' in data and data['password']:
            user.set_password(data['password'])
            log_desc += 'Password diubah, '
            is_updated = True

        db.session.commit() # Commit transaksi utama
        
        # --- FIX 3: Panggil Log setelah Commit sukses ---
        if is_updated:
            record_log(
                action_type='USER_UPDATE',
                description=log_desc.strip().rstrip(',') # Bersihkan koma & spasi di akhir
            )
        
        return jsonify({'message': f'User ID {user_id} berhasil diperbarui.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error saat memperbarui user: {str(e)}'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(user_id):
    """[DELETE] Menghapus atau menonaktifkan pengguna."""
    user = User.query.get_or_404(user_id)
    
    try:
        # Soft Delete: Menonaktifkan user
        user.is_active = False 
        db.session.commit() # Commit transaksi utama
        
        # --- FIX 4: Panggil Log setelah Commit sukses ---
        record_log(
            action_type='USER_DELETE',
            description=f'Menonaktifkan user: {user.username} (ID {user_id}). (Soft Delete)'
        )
        
        return jsonify({'message': f'User ID {user_id} berhasil dinonaktifkan.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error saat menghapus user: {str(e)}'}), 500

# --- 3. HELPER ENDPOINT (OPSIONAL) ---

@admin_bp.route('/roles', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_roles():
    """Mengambil daftar semua Role yang tersedia."""
    roles = Role.query.all()
    result = [{'role_id': r.role_id, 'nama_role': r.nama_role} for r in roles]
    return jsonify(result), 200