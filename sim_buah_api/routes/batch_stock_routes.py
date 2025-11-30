# /sim_buah_api/routes/batch_stock_routes.py

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sim_buah_api.database import db
from sim_buah_api.models import BatchStok, Buah, User
from sqlalchemy import func

batch_stock_bp = Blueprint('batch_stock', __name__, url_prefix='/api/batch-stock')

# =========================
# Helper: Ambil role user
# =========================
def get_user_role(user_id):
    user = User.query.get(user_id)
    return user.role.nama_role if user else None

# =========================
# Get all batch stock (FIFO)
# =========================
@batch_stock_bp.route('/', methods=['GET'])
@jwt_required()
def get_batch_stock():
    user_id = get_jwt_identity()
    role = get_user_role(user_id)

    batches = BatchStok.query.join(Buah).order_by(BatchStok.tanggal_masuk_batch.asc()).all()

    result = [
        {
            "batch_id": batch.batch_id,
            "masuk_id": batch.masuk_id,
            "buah_id": batch.buah_id,
            "nama_buah": batch.jenis_buah.nama_buah,
            "tanggal_masuk_batch": batch.tanggal_masuk_batch.isoformat(),
            "stok_awal": float(batch.stok_awal),
            "stok_saat_ini": float(batch.stok_saat_ini),
            "kualitas": batch.kualitas
        }
        for batch in batches
    ]

    return jsonify({"data": result, "role": role})

# ==========================================================
# Endpoint Baru: Get Available Batches for Transaction
# URL: /api/batch-stock/available
# ==========================================================
@batch_stock_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_batches():
    """
    Mengambil batch yang memiliki stok_saat_ini > 0
    Beserta nama buah dan harga_jual
    """
    available_batches = (
        db.session.query(
            BatchStok,
            Buah.nama_buah,
            Buah.harga_jual  # Pastikan field harga_jual ada di model Buah
        )
        .join(Buah)
        .filter(BatchStok.stok_saat_ini > 0)
        .order_by(BatchStok.tanggal_masuk_batch.asc())
        .all()
    )

    result = [
        {
            "batch_id": batch.batch_id,
            "buah_id": batch.buah_id,
            "nama_buah": nama_buah,
            "tanggal_masuk": batch.tanggal_masuk_batch.isoformat(),
            "stok_tersedia": float(batch.stok_saat_ini),
            "stok_saat_ini": float(batch.stok_saat_ini),
            "kualitas": batch.kualitas,
            "harga_jual": float(harga_jual) if harga_jual else 0.0
        }
        for batch, nama_buah, harga_jual in available_batches
    ]

    # Endpoint ini mengembalikan array langsung (tidak dibungkus "data")
    return jsonify(result)
