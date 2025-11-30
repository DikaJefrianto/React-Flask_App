from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from decimal import Decimal

from sim_buah_api.database import db
from sim_buah_api.models import (
    Buah, Supplier, Pelanggan, User, LogAktivitas,
    BarangMasuk, BatchStok,
    BarangKeluar, DetailKeluar
)
from ..utils.log_helper import record_log  # FIX: import helper log

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


# =========================
# HELPER: Ambil role user
# =========================
def get_user_role(user_id):
    user = User.query.get(user_id)
    return user.role.nama_role if user else None


# =========================
# BARANG MASUK (GET)
# =========================
@inventory_bp.route("/masuk", methods=["GET"])
@jwt_required()
def list_barang_masuk():
    user_id = get_jwt_identity()
    role = get_user_role(user_id)

    masuk_list = BarangMasuk.query.order_by(BarangMasuk.masuk_id.desc()).all()
    result = []

    for trx in masuk_list:
        result.append({
            "id": trx.masuk_id,
            "tanggal": trx.tanggal_transaksi.isoformat(),
            "supplier": trx.pemasok.nama_supplier,
            "petugas": trx.petugas_masuk.nama_lengkap,
            "total_biaya": float(trx.total_biaya),
            "batches": [
                {
                    "buah": batch.jenis_buah.nama_buah,
                    "stok_awal": float(batch.stok_awal),
                    "stok_saat_ini": float(batch.stok_saat_ini),
                    "kualitas": batch.kualitas
                } for batch in trx.batches
            ]
        })

    return jsonify({"data": result, "role": role})


# =========================
# BARANG MASUK (POST)
# =========================
@inventory_bp.route("/masuk", methods=["POST"])
@jwt_required()
def create_barang_masuk():
    user_id = get_jwt_identity()
    role = get_user_role(user_id)

    # Hanya Admin & Petugas Gudang
    if role not in ["Admin", "Petugas Gudang"]:
        return jsonify({"error": "Akses ditolak"}), 403

    data = request.json
    supplier_id = data.get("supplier_id")
    items = data.get("items", [])
    total_biaya = Decimal(str(data.get("total_biaya", 0)))

    if not supplier_id or not items:
        return jsonify({"error": "Data supplier atau item tidak lengkap"}), 400

    try:
        # Buat transaksi BarangMasuk
        trx = BarangMasuk(
            tanggal_transaksi=date.today(),
            supplier_id=supplier_id,
            user_id=user_id,
            total_biaya=total_biaya
        )
        db.session.add(trx)
        db.session.flush()  # Mendapatkan trx.masuk_id

        buah_masuk_list = []

        # Buat batch stok untuk tiap item
        for item in items:
            buah = Buah.query.get(item["buah_id"])
            stok_awal = Decimal(str(item["stok_awal"]))

            if stok_awal <= 0:
                db.session.rollback()
                return jsonify({"error": f"Stok awal untuk {buah.nama_buah} harus > 0"}), 400

            batch = BatchStok(
                masuk_id=trx.masuk_id,
                buah_id=buah.buah_id,
                tanggal_masuk_batch=date.today(),
                stok_awal=stok_awal,
                stok_saat_ini=stok_awal,
                kualitas=item.get("kualitas")
            )
            db.session.add(batch)

            # Update stok total master buah
            buah.stok_total += stok_awal
            buah_masuk_list.append(f'{buah.nama_buah} ({stok_awal} kg)')

        db.session.commit()  # Commit transaksi utama

        # Catat log aktivitas
        record_log(
            action_type='TRX_MASUK_CREATE',
            description=f'Mencatat barang masuk ID {trx.masuk_id} dari Supplier {trx.pemasok.nama_supplier}. Item: {", ".join(buah_masuk_list)}'
        )

        return jsonify({"msg": "Barang masuk berhasil dibuat", "id": trx.masuk_id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
