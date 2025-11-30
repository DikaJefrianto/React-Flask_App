from sim_buah_api.database import db
from sim_buah_api import create_app

app = create_app()

with app.app_context():
    # Hapus semua tabel
    db.drop_all()
    
    # Buat semua tabel lagi
    db.create_all()
    print("Database telah direset!")
