from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from datetime import date
from sim_buah_api.models import BatchStok, Buah

monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')

@monitor_bp.route("/batch_stock", methods=["GET"])
@jwt_required()
def get_batch_stock():
    try:
        today = date.today()
        batches = BatchStok.query.join(Buah, BatchStok.buah_id == Buah.buah_id).all()

        result = []
        for b in batches:
            if b.stok_saat_ini <= 0:
                continue

            umur_batch = (today - b.tanggal_masuk_batch).days
            umur_max = b.jenis_buah.umur_simpan_hari
            days_left = umur_max - umur_batch
            persentase_sisa = days_left / umur_max if umur_max else 0

            if persentase_sisa <= 0.2:
                status = "Kritis"
            elif persentase_sisa <= 0.5:
                status = "Sedang"
            else:
                status = "Aman"

            result.append({
                "batch_id": b.batch_id,
                "buah": b.jenis_buah.nama_buah,
                "stok_saat_ini": float(b.stok_saat_ini),
                "tanggal_masuk": b.tanggal_masuk_batch.strftime("%Y-%m-%d"),
                "umur_simpan_hari": umur_max,
                "days_left": days_left,
                "status_fifo": status
            })

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
