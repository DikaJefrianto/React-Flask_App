from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import extract, func, case, or_
from ..database import db
from ..models import (
    User, Supplier, Pelanggan, Buah,
    LogAktivitas, BarangKeluar, DetailKeluar, BatchStok
)
from datetime import datetime, date

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    now = datetime.now()
    today = date.today()

    # ======================================================
    # 1. KPI & STATS UMUM (Admin, Manajer, Petugas)
    # ======================================================
    active_users_count = User.query.filter(
        (User.is_active == True) | (User.is_active == 1)
    ).count()
    total_suppliers = Supplier.query.count()
    total_customers = Pelanggan.query.count()
    total_stock = db.session.query(func.coalesce(func.sum(Buah.stok_total), 0)).scalar()

    # ======================================================
    # 2. Manager Stats (Manajer)
    # ======================================================
    total_penjualan_bulan_ini = db.session.query(
        func.coalesce(func.sum(BarangKeluar.total_penjualan), 0)
    ).filter(
        extract('month', BarangKeluar.tanggal_transaksi) == now.month,
        extract('year', BarangKeluar.tanggal_transaksi) == now.year
    ).scalar()

    kualitas_rata = db.session.query(
        func.avg(
            case(
                (BatchStok.kualitas == "Grade A", 3),
                (BatchStok.kualitas == "Grade B", 2),
                (BatchStok.kualitas == "Grade C", 1),
                else_=0
            )
        )
    ).scalar()

    pesanan_dibatalkan = BarangKeluar.query.filter_by(status_pesanan="Batal").count()

    fifo_kritis = BatchStok.query.filter(
        BatchStok.stok_saat_ini > 0
    ).order_by(BatchStok.tanggal_masuk_batch.asc()).limit(5).all()

    fifo_kritis_list = [
        {
            "buah": batch.jenis_buah.nama_buah,
            "stok_saat_ini": float(batch.stok_saat_ini),
            "tanggal_masuk": batch.tanggal_masuk_batch.strftime("%Y-%m-%d"),
            "kualitas": batch.kualitas
        }
        for batch in fifo_kritis
    ]

    grafik_penjualan = db.session.query(
        extract('month', BarangKeluar.tanggal_transaksi).label('bulan'),
        func.sum(BarangKeluar.total_penjualan).label('total')
    ).group_by('bulan').order_by('bulan').all()

    grafik_penjualan_list = [
        {"bulan": int(row.bulan), "total": float(row.total)}
        for row in grafik_penjualan
    ]

    data_laporan = {
        "total_transaksi_masuk": BarangKeluar.query.count(),
        "total_transaksi_keluar": BarangKeluar.query.count(),
        "total_buah_jenis": Buah.query.count(),
    }

    # ======================================================
    # 3. Petugas Gudang Stats
    # ======================================================
    STATUS_PERLU_DITAMPILKAN = ['Diproses', 'diproses']

    pesanan_hari_ini_qs = BarangKeluar.query.filter(
        BarangKeluar.tanggal_transaksi == today,
        BarangKeluar.status_pesanan.in_(STATUS_PERLU_DITAMPILKAN)
    ).all()

    pesanan_hari_ini_list = [
        {
            "id": trx.keluar_id,
            "pelanggan": trx.pembeli.nama_pelanggan if trx.pembeli else "N/A",
            "waktu": "Hari Ini",
            "status": trx.status_pesanan
        }
        for trx in pesanan_hari_ini_qs
    ]

    pesanan_menunggu_count = BarangKeluar.query.filter(
        BarangKeluar.tanggal_transaksi == today,
        BarangKeluar.status_pesanan.in_(STATUS_PERLU_DITAMPILKAN)
    ).count()

    # ======================================================
    # 4. System Health & Log Aktivitas
    # ======================================================
    system_health = {
        "server": {
            "name": "Status Server",
            "detail": "API Flask & Database",
            "status_text": "Online",
            "status_color": "bg-green-600 text-white"
        },
        "database": {
            "name": "Database",
            "detail": "MySQL / MariaDB",
            "status_text": "Online",
            "status_color": "bg-green-600 text-white"
        }
    }

    logs = LogAktivitas.query.order_by(LogAktivitas.timestamp.desc()).limit(5).all()
    recent_activities = []
    for log in logs:
        action_type = "update"
        if "tambah" in log.deskripsi.lower() or "create" in log.jenis_aksi.lower():
            action_type = "create"
        elif "hapus" in log.deskripsi.lower():
            action_type = "delete"

        recent_activities.append({
            "user": log.user.nama_lengkap if log.user else "Unknown",
            "action": log.deskripsi,
            "time": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "type": action_type
        })

    # ======================================================
    # RETURN JSON
    # ======================================================
    return jsonify({
        "kpi_data": {
            "active_users": active_users_count,
            "total_suppliers": total_suppliers,
            "total_customers": total_customers,
            "total_stock": float(total_stock)
        },
        "manager_stats": {
            "total_stock_now": float(total_stock),
            "total_sales_this_month": float(total_penjualan_bulan_ini),
            "average_quality": float(kualitas_rata or 0),
            "canceled_orders": pesanan_dibatalkan,
            "fifo_critical_batches": fifo_kritis_list,
            "sales_chart": grafik_penjualan_list,
            "report_summary": data_laporan
        },
        "petugas_stats": {
            "total_stock": float(total_stock),
            "pesanan_menunggu_proses": pesanan_menunggu_count,
            "fifo_kritis_count": len(fifo_kritis_list),
            "pesanan_hari_ini": pesanan_hari_ini_list
        },
        "system_health": system_health,
        "recent_activities": recent_activities
    })
