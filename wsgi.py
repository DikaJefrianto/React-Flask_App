# /backend_flask/wsgi.py

# Import Factory dan db dari package sim_buah_api
from sim_buah_api.__init__ import create_app, db
# Import Models harus ABSOLUT dari package induk!
from sim_buah_api.models import User, Role, Buah, Supplier, Pelanggan, LogAktivitas 
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Ini adalah perbaikan utamanya ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Buat instance aplikasi (panggilan ke Factory)
app = create_app()

def setup_database():
    """Fungsi untuk inisialisasi database dan seeding data awal."""
    with app.app_context():
        
        # 1. Buat Tabel Database (jika belum ada di PostgreSQL)
        print("Mencoba membuat SEMUA tabel database (db.create_all())...")
        db.create_all() 
        print("Inisialisasi tabel selesai.")
        
        # 2. Seeding Data Awal (Roles)
        if Role.query.count() == 0:
            print("Seeding Roles...")
            roles = [
                Role(nama_role='Admin', deskripsi='Akses penuh ke semua modul dan konfigurasi.'),
                Role(nama_role='Manajer', deskripsi='Akses ke Laporan dan Transaksi.'),
                Role(nama_role='Petugas Gudang', deskripsi='Akses ke Transaksi Barang Masuk dan Keluar.')
            ]
            db.session.add_all(roles)
            db.session.commit()
            print("3 Roles berhasil ditambahkan.")
            
        # 3. Seeding User Admin Default
        admin_role = Role.query.filter_by(nama_role='Admin').first()
        if admin_role and not User.query.filter_by(username='admin').first():
             print("Menambahkan User Admin Default 'admin'...")
             admin = User(user_id=1, role_id=admin_role.role_id, username='admin', nama_lengkap='Super Admin Sistem')
             admin.set_password('12345678') # Sandi '12345678'
             db.session.add(admin)
             db.session.commit()
             print(f"User '{admin.username}' berhasil ditambahkan (Sandi: 12345678).")

if __name__ == '__main__':
    # Lakukan setup database dan seeding
    setup_database()
    
    # Jalankan server Flask
    print("\n--- Flask Server Running ---")
    print(f"Akses API Status: http://127.0.0.1:5000/api/status")
    print(f"Akses Login API: http://127.0.0.1:5000/api/auth/login")
    app.run(debug=True,host="0.0.0.0", port=5000)