# /backend_flask/sim_buah_api/routes/transaksi_bp.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from decimal import Decimal

from sim_buah_api.database import db
from sim_buah_api.models import BarangKeluar, DetailKeluar, BatchStok, User, Pelanggan
# FIX KRITIS: Import record_log dari helper file
from ..utils.log_helper import record_log 

transaksi_bp = Blueprint('transaksi', __name__, url_prefix='/api/transaksi')


# =========================
# Helper: Ambil role user
# =========================
def get_user_role(user_id):
    user = User.query.get(user_id)
    return user.role.nama_role if user else "unknown"


# =========================
# GET – Semua Transaksi Keluar
# =========================
@transaksi_bp.route("/keluar", methods=["GET"])
def get_barang_keluar():
    # ... (Logika READ tetap sama)
    try:
        data = BarangKeluar.query.all()
        result = []
        for row in data:
            result.append({
                "keluar_id": row.keluar_id,
                "pelanggan": row.pembeli.nama_pelanggan if row.pembeli else None,
                "petugas": row.petugas_keluar.nama_lengkap if row.petugas_keluar else None,
                "status": row.status_pesanan,
                "tanggal": row.tanggal_transaksi.strftime("%Y-%m-%d") if row.tanggal_transaksi else None,
                "total_penjualan": float(row.total_penjualan) if row.total_penjualan else 0
            })
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================
# POST – Buat Transaksi Baru (Safe & Logged) (LOG DITERAPKAN)
# =========================
@transaksi_bp.route("/keluar", methods=["POST"])
@jwt_required()
def create_barang_keluar_safe():
    user_id = get_jwt_identity()
    role = get_user_role(user_id)

    if role not in ["Admin", "Petugas Gudang"]:
        return jsonify({"error": "Akses ditolak"}), 403

    data = request.json
    pelanggan_id = data.get("pelanggan_id")
    items = data.get("items", [])
    total_penjualan = Decimal(str(data.get("total_penjualan", 0)))

    if not pelanggan_id:
        return jsonify({"error": "Pelanggan wajib dipilih"}), 400
    if not items:
        return jsonify({"error": "Item tidak boleh kosong"}), 400

    try:
        # Cari nama pelanggan untuk deskripsi log
        pelanggan = Pelanggan.query.get(pelanggan_id)
        pelanggan_name = pelanggan.nama_pelanggan if pelanggan else "ID Tidak Dikenal"

        # Buat transaksi baru
        trx = BarangKeluar(
            tanggal_transaksi=date.today(),
            pelanggan_id=pelanggan_id,
            user_id=user_id,
            status_pesanan="Diproses",
            total_penjualan=total_penjualan
        )
        db.session.add(trx)
        db.session.flush()

        # Proses setiap item (kurangi stok dan buat detail)
        for idx, item in enumerate(items):
            # ... (Logic validasi stok & pengurangan)
            batch_id = int(item.get("batch_id"))
            qty = Decimal(str(item.get("jumlah", 0)))
            harga = Decimal(str(item.get("harga_satuan", 0)))

            batch = BatchStok.query.get(batch_id)
            if not batch:
                db.session.rollback()
                return jsonify({"error": f"Batch {batch_id} tidak ditemukan"}), 400
            if qty <= 0:
                db.session.rollback()
                return jsonify({"error": f"Jumlah item ke-{idx+1} harus lebih dari 0"}), 400
            if batch.stok_saat_ini < qty:
                db.session.rollback()
                return jsonify({"error": f"Stok batch {batch_id} tidak cukup. Tersisa: {batch.stok_saat_ini}"}), 400

            # Kurangi stok
            batch.stok_saat_ini -= qty
            batch.jenis_buah.stok_total -= qty

            # Tambahkan detail keluar
            detail = DetailKeluar(
                keluar_id=trx.keluar_id,
                batch_id=batch_id,
                jumlah_keluar=qty,
                harga_jual_satuan=harga
            )
            db.session.add(detail)

        db.session.commit() # Commit transaksi utama

        # --- FIX 1: Catat Log (CREATE) ---
        record_log(
            action_type='TRX_KELUAR_CREATE',
            description=f'Membuat pesanan ID {trx.keluar_id} untuk pelanggan: {pelanggan_name}. Total: {total_penjualan}'
        )

        return jsonify({"status": "success", "msg": f"Transaksi ID {trx.keluar_id} berhasil dibuat"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# PUT – Update Status (LOG DITERAPKAN)
# =========================
@transaksi_bp.route("/keluar/<int:id>", methods=["OPTIONS", "PUT"])
@jwt_required()
def update_status_keluar(id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user_id = get_jwt_identity()
    data = request.json
    status_baru = data.get("status")

    if not status_baru:
        return jsonify({"error": "Status baru tidak boleh kosong"}), 400

    try:
        trx = BarangKeluar.query.get_or_404(id)
        status_lama = trx.status_pesanan

        # 1. LOGIKA PENGEMBALIAN STOK SAAT DIBATALKAN
        if status_lama != "Batal" and status_baru == "Batal":
            for detail in trx.detail_keluar:
                batch = detail.batch_asal
                if batch:
                    qty = detail.jumlah_keluar
                    batch.stok_saat_ini += qty
                    batch.jenis_buah.stok_total += qty
        
        # 2. Perbarui status transaksi
        trx.status_pesanan = status_baru
        db.session.commit()
        
        # --- FIX 2: Catat Log (UPDATE STATUS) ---
        record_log(
            action_type='TRX_KELUAR_UPDATE',
            description=f'Mengubah status Pesanan ID {id} dari {status_lama} menjadi {status_baru}.'
        )

        return jsonify({"status": "success", "msg": f"Status transaksi ID {id} berhasil diperbarui menjadi {status_baru}"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# DELETE – Hapus Transaksi (LOG DITERAPKAN)
# =========================
@transaksi_bp.route("/keluar/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_barang_keluar(id):
    try:
        trx = BarangKeluar.query.get_or_404(id)
        pelanggan_name = trx.pembeli.nama_pelanggan if trx.pembeli else "N/A"

        # Logika pengembalian stok hanya berjalan jika status BUKAN "Batal"
        if trx.status_pesanan != "Batal":
            for detail in trx.detail_keluar:
                batch = detail.batch_asal
                if batch:
                    qty = detail.jumlah_keluar
                    batch.stok_saat_ini += qty
                    batch.jenis_buah.stok_total += qty
        
        # Lanjutkan menghapus transaksi dari database
        db.session.delete(trx)
        db.session.commit()

        # --- FIX 3: Catat Log (DELETE) ---
        record_log(
            action_type='TRX_KELUAR_DELETE',
            description=f'Menghapus Pesanan ID {id} (Pelanggan: {pelanggan_name}). Stok dikembalikan.'
        )

        return jsonify({"status": "success", "msg": f"Transaksi ID {id} berhasil dihapus"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500