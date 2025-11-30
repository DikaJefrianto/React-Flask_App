from flask_jwt_extended import get_jwt_identity
from ..database import db
from ..models import LogAktivitas

def record_log(action_type, description):
    """
    Fungsi helper untuk mencatat aktivitas ke tabel LogAktivitas.
    Dipanggil setelah db.session.commit() dari transaksi utama.
    """
    try:
        # PENTING: get_jwt_identity() akan memberikan user_id dari token JWT
        user_id = get_jwt_identity() 
        
        # Cek apakah user_id tersedia
        if not user_id:
            # Jika tidak ada user ID (misalnya dipanggil di context non-JWT),
            # gunakan ID default atau batalkan log.
            # Kita asumsikan semua aksi CRUD harus melalui JWT.
            print("ERROR: record_log dipanggil tanpa User ID (JWT Identity).")
            return
            
        log = LogAktivitas(
            user_id=user_id,
            jenis_aksi=action_type, # e.g., 'USER_CREATE', 'TRX_MASUK_POST'
            deskripsi=description
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Jika gagal mencatat log, cetak error tetapi JANGAN HENTIKAN proses 
        # API utama (karena transaksi utama sudah committed).
        print(f"ERROR: Gagal mencatat log aktivitas: {e}")
        db.session.rollback()