from flask import Blueprint, request, jsonify
from ..models import db, Buah, Supplier, Pelanggan
from decimal import Decimal
from flask_jwt_extended import jwt_required
# FIX KRITIS: Import record_log dari file helper
from ..utils.log_helper import record_log 

master_bp = Blueprint('master', __name__, url_prefix='/api/master')


# =========================
# CRUD Buah (Log Diterapkan)
# =========================
@master_bp.route('/buah', methods=['GET'])
@jwt_required()
def get_buah():
    # ... (READ logic tetap sama)
    buah_list = Buah.query.all()
    return jsonify([{
        "buah_id": b.buah_id,
        "nama_buah": b.nama_buah,
        "satuan": b.satuan,
        "harga_satuan": float(b.harga_satuan),
        "umur_simpan_hari": b.umur_simpan_hari,
        "stok_total": float(b.stok_total)
    } for b in buah_list])


@master_bp.route('/buah', methods=['POST'])
@jwt_required()
def add_buah():
    data = request.json
    try:
        new_buah = Buah(
            nama_buah=data['nama_buah'],
            satuan=data['satuan'],
            harga_satuan=Decimal(data.get('harga_satuan', '0.00')),
            umur_simpan_hari=int(data['umur_simpan_hari']),
            stok_total=Decimal(data.get('stok_total', '0.00'))
        )
        db.session.add(new_buah)
        db.session.commit()
        
        # FIX 1: Catat Log (CREATE)
        record_log(
            action_type='BUAH_CREATE',
            description=f"Menambahkan jenis buah baru: {data['nama_buah']}"
        )
        
        return jsonify({"msg": "Buah berhasil ditambahkan", "id": new_buah.buah_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@master_bp.route('/buah/<int:buah_id>', methods=['PUT'])
@jwt_required()
def update_buah(buah_id):
    data = request.json
    buah = Buah.query.get_or_404(buah_id)
    try:
        # Catat nama sebelum update untuk deskripsi log
        old_name = buah.nama_buah
        
        buah.nama_buah = data.get('nama_buah', buah.nama_buah)
        buah.satuan = data.get('satuan', buah.satuan)
        buah.harga_satuan = Decimal(data.get('harga_satuan', buah.harga_satuan))
        buah.umur_simpan_hari = int(data.get('umur_simpan_hari', buah.umur_simpan_hari))
        buah.stok_total = Decimal(data.get('stok_total', buah.stok_total))
        db.session.commit()
        
        # FIX 2: Catat Log (UPDATE)
        record_log(
            action_type='BUAH_UPDATE',
            description=f"Memperbarui data buah: {buah.nama_buah} (ID {buah_id})"
        )
        
        return jsonify({"msg": "Buah berhasil diperbarui"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@master_bp.route('/buah/<int:buah_id>', methods=['DELETE'])
@jwt_required()
def delete_buah(buah_id):
    buah = Buah.query.get_or_404(buah_id)
    try:
        nama_buah = buah.nama_buah # Ambil nama sebelum delete
        db.session.delete(buah)
        db.session.commit()
        
        # FIX 3: Catat Log (DELETE)
        record_log(
            action_type='BUAH_DELETE',
            description=f"Menghapus jenis buah: {nama_buah} (ID {buah_id})"
        )
        
        return jsonify({"msg": "Buah berhasil dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# =========================
# CRUD Supplier (Log Diterapkan)
# =========================
@master_bp.route('/supplier', methods=['GET'])
@jwt_required()
def get_supplier():
    # ... (READ logic tetap sama)
    suppliers = Supplier.query.all()
    return jsonify([{
        "supplier_id": s.supplier_id,
        "nama_supplier": s.nama_supplier,
        "alamat": s.alamat,
        "kontak": s.kontak
    } for s in suppliers])


@master_bp.route('/supplier', methods=['POST'])
@jwt_required()
def add_supplier():
    data = request.json
    try:
        new_supplier = Supplier(
            nama_supplier=data['nama_supplier'],
            alamat=data['alamat'],
            kontak=data.get('kontak', '')
        )
        db.session.add(new_supplier)
        db.session.commit()
        
        # FIX 4: Catat Log (CREATE)
        record_log(
            action_type='SUPPLIER_CREATE',
            description=f"Menambahkan supplier baru: {data['nama_supplier']}"
        )
        
        return jsonify({"msg": "Supplier berhasil ditambahkan", "id": new_supplier.supplier_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@master_bp.route('/supplier/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    data = request.json
    supplier = Supplier.query.get_or_404(supplier_id)
    try:
        supplier.nama_supplier = data.get('nama_supplier', supplier.nama_supplier)
        supplier.alamat = data.get('alamat', supplier.alamat)
        supplier.kontak = data.get('kontak', supplier.kontak)
        db.session.commit()
        
        # FIX 5: Catat Log (UPDATE)
        record_log(
            action_type='SUPPLIER_UPDATE',
            description=f"Memperbarui data supplier: {supplier.nama_supplier} (ID {supplier_id})"
        )
        
        return jsonify({"msg": "Supplier berhasil diperbarui"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@master_bp.route('/supplier/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    try:
        nama_supplier = supplier.nama_supplier
        db.session.delete(supplier)
        db.session.commit()
        
        # FIX 6: Catat Log (DELETE)
        record_log(
            action_type='SUPPLIER_DELETE',
            description=f"Menghapus supplier: {nama_supplier} (ID {supplier_id})"
        )
        
        return jsonify({"msg": "Supplier berhasil dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# =========================
# CRUD Pelanggan (Log Diterapkan)
# =========================
@master_bp.route('/pelanggan', methods=['GET'])
@jwt_required()
def get_pelanggan():
    # ... (READ logic tetap sama)
    customers = Pelanggan.query.all()
    return jsonify([{
        "pelanggan_id": c.pelanggan_id,
        "nama_pelanggan": c.nama_pelanggan,
        "alamat": c.alamat,
        "telepon": c.telepon
    } for c in customers])


@master_bp.route('/pelanggan', methods=['POST'])
@jwt_required()
def add_pelanggan():
    data = request.json
    try:
        new_cust = Pelanggan(
            nama_pelanggan=data['nama_pelanggan'],
            alamat=data['alamat'],
            telepon=data.get('telepon', '')
        )
        db.session.add(new_cust)
        db.session.commit()
        
        # FIX 7: Catat Log (CREATE)
        record_log(
            action_type='PELANGGAN_CREATE',
            description=f"Menambahkan pelanggan baru: {data['nama_pelanggan']}"
        )
        
        return jsonify({"msg": "Pelanggan berhasil ditambahkan", "id": new_cust.pelanggan_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@master_bp.route('/pelanggan/<int:pelanggan_id>', methods=['PUT'])
@jwt_required()
def update_pelanggan(pelanggan_id):
    data = request.json
    cust = Pelanggan.query.get_or_404(pelanggan_id)
    try:
        cust.nama_pelanggan = data.get('nama_pelanggan', cust.nama_pelanggan)
        cust.alamat = data.get('alamat', cust.alamat)
        cust.telepon = data.get('telepon', cust.telepon)
        db.session.commit()
        
        # FIX 8: Catat Log (UPDATE)
        record_log(
            action_type='PELANGGAN_UPDATE',
            description=f"Memperbarui data pelanggan: {cust.nama_pelanggan} (ID {pelanggan_id})"
        )
        
        return jsonify({"msg": "Pelanggan berhasil diperbarui"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@master_bp.route('/pelanggan/<int:pelanggan_id>', methods=['DELETE'])
@jwt_required()
def delete_pelanggan(pelanggan_id):
    cust = Pelanggan.query.get_or_404(pelanggan_id)
    try:
        nama_pelanggan = cust.nama_pelanggan
        db.session.delete(cust)
        db.session.commit()
        
        # FIX 9: Catat Log (DELETE)
        record_log(
            action_type='PELANGGAN_DELETE',
            description=f"Menghapus pelanggan: {nama_pelanggan} (ID {pelanggan_id})"
        )
        
        return jsonify({"msg": "Pelanggan berhasil dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400