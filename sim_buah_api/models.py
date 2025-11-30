# /backend_flask/sim_buah_api/models.py

from datetime import datetime, date
from decimal import Decimal

# PENTING: Import db dan bcrypt dari file database yang berisi extensions
from .database import db, bcrypt 


# ====================================================================
# A. MASTER DATA UTAMA (USER & ROLE)
# ====================================================================

class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer, primary_key=True)
    nama_role = db.Column(db.String(50), unique=True, nullable=False)
    deskripsi = db.Column(db.String(255))
    
    # Relasi balik
    users = db.relationship('User', backref='role', lazy=True)

class User(db.Model):
    __tablename__ = 'user_account'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relasi balik untuk Transaksi
    barang_masuk = db.relationship('BarangMasuk', backref='petugas_masuk', lazy=True)
    barang_keluar = db.relationship('BarangKeluar', backref='petugas_keluar', lazy=True)
    logs = db.relationship('LogAktivitas', backref='user', lazy=True)
    
    # --- FUNGSI KRITIS: FIX ValueError: Invalid salt ---
    def set_password(self, password):
        """Membuat password hash menggunakan Bcrypt."""
        # Gunakan bcrypt yang diimpor dari database.py
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Memverifikasi password hash."""
        return bcrypt.check_password_hash(self.password_hash, password)


class LogAktivitas(db.Model):
    __tablename__ = 'log_aktivitas'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.user_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    jenis_aksi = db.Column(db.String(50), nullable=False) # e.g., 'TRX_MASUK', 'USER_CREATE'
    deskripsi = db.Column(db.String(255), nullable=False)

# ====================================================================
# B. MASTER DATA PENDUKUNG (FR-03, FR-04, FR-05)
# ====================================================================

class Buah(db.Model):
    __tablename__ = 'master_buah'
    buah_id = db.Column(db.Integer, primary_key=True)
    nama_buah = db.Column(db.String(100), unique=True, nullable=False)
    satuan = db.Column(db.String(10), nullable=False) # e.g., 'kg', 'box'
    umur_simpan_hari = db.Column(db.Integer, nullable=False)
    stok_total = db.Column(db.Numeric(10, 2), default=Decimal('0.00'), nullable=False) # Agregat stok
    harga_satuan = db.Column(db.Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    # Relasi Balik
    batches = db.relationship('BatchStok', backref='jenis_buah', lazy=True)

class Supplier(db.Model):
    __tablename__ = 'master_supplier'
    supplier_id = db.Column(db.Integer, primary_key=True)
    nama_supplier = db.Column(db.String(100), unique=True, nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    kontak = db.Column(db.String(50))
    
    # Relasi Balik
    barang_masuk_records = db.relationship('BarangMasuk', backref='pemasok', lazy=True)

class Pelanggan(db.Model):
    __tablename__ = 'master_pelanggan'
    pelanggan_id = db.Column(db.Integer, primary_key=True)
    nama_pelanggan = db.Column(db.String(100), unique=True, nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    telepon = db.Column(db.String(50))
    
    # Relasi Balik
    barang_keluar_records = db.relationship('BarangKeluar', backref='pembeli', lazy=True)

# ====================================================================
# C. TRANSAKSI (FIFO LOGIC)
# ====================================================================

class BarangMasuk(db.Model):
    __tablename__ = 'trx_barang_masuk'
    masuk_id = db.Column(db.Integer, primary_key=True)
    tanggal_transaksi = db.Column(db.Date, default=date.today, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('master_supplier.supplier_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.user_id'), nullable=False) # Petugas Gudang/Admin
    total_biaya = db.Column(db.Numeric(10, 2), default=Decimal('0.00')) # Total Biaya Pembelian

    # Relasi Balik
    batches = db.relationship('BatchStok', backref='barang_masuk', lazy=True)

class BatchStok(db.Model):
    __tablename__ = 'batch_stok'
    batch_id = db.Column(db.Integer, primary_key=True)
    masuk_id = db.Column(db.Integer, db.ForeignKey('trx_barang_masuk.masuk_id'), nullable=False)
    buah_id = db.Column(db.Integer, db.ForeignKey('master_buah.buah_id'), nullable=False)
    
    tanggal_masuk_batch = db.Column(db.Date, nullable=False) # KUNCI UTAMA FIFO
    # tanggal_kadaluarsa = db.Column(db.Date)
    
    stok_awal = db.Column(db.Numeric(10, 2), nullable=False)
    stok_saat_ini = db.Column(db.Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    kualitas = db.Column(db.String(50)) # e.g., 'Grade A', 'Grade B'

    # Relasi Balik
    detail_keluar_records = db.relationship(
    'DetailKeluar',
    backref='batch_asal',
    lazy=True,
    cascade="all, delete-orphan"
)

    
    # Constraint Kritis: Stok saat ini tidak boleh negatif
    __table_args__ = (
        db.CheckConstraint(stok_saat_ini >= Decimal('0.00'), name='stok_must_be_non_negative'),
    )

class BarangKeluar(db.Model):
    __tablename__ = 'trx_barang_keluar'
    keluar_id = db.Column(db.Integer, primary_key=True)
    tanggal_transaksi = db.Column(db.Date, default=date.today, nullable=False)
    pelanggan_id = db.Column(db.Integer, db.ForeignKey('master_pelanggan.pelanggan_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.user_id'), nullable=False)
    status_pesanan = db.Column(db.String(50), default='Diproses') # e.g., 'Diproses', 'Terkirim', 'Batal'
    total_penjualan = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))

    # Relasi Balik
    pelanggan = db.relationship("Pelanggan", backref="transaksi_keluar")
    detail_keluar = db.relationship(
    'DetailKeluar',
    backref='pesanan_keluar',
    lazy=True,
    cascade="all, delete-orphan"  # <--- penting
)


class DetailKeluar(db.Model):
    __tablename__ = 'trx_detail_keluar'
    detail_id = db.Column(db.Integer, primary_key=True)
    keluar_id = db.Column(db.Integer, db.ForeignKey('trx_barang_keluar.keluar_id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch_stok.batch_id'), nullable=False) # Kunci audit FIFO
    
    jumlah_keluar = db.Column(db.Numeric(10, 2), nullable=False)
    harga_jual_satuan = db.Column(db.Numeric(10, 2), nullable=False)