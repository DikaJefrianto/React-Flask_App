#!/bin/sh

echo "=== AUTO MIGRATION START ==="

# Pastikan Flask tahu entry point
export FLASK_APP=app.py
export FLASK_ENV=production

# Jika folder migrations belum ada → init
if [ ! -d "migrations" ]; then
  echo "Migrations not found, initializing..."
  flask db init
fi

# Buat ulang migration dari model
flask db migrate -m "auto migration"

# Terapkan ke MySQL Railway
flask db upgrade

echo "=== AUTO MIGRATION DONE ==="


