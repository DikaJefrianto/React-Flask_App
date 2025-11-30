#!/bin/sh

echo "=== AUTO MIGRATION START ==="

export FLASK_APP=app.py
export FLASK_ENV=production

# Hapus migrations lama jika ada
if [ -d "migrations" ]; then
  echo "Old migrations found, removing..."
  rm -rf migrations
fi

# Init migrations baru
echo "Initializing new migrations..."
flask db init

# Buat migration baru dari model saat ini
echo "Generating new migration..."
flask db migrate -m "auto migration" || echo "No changes detected in models."

# Terapkan migration ke database
echo "Applying migration..."
flask db upgrade

echo "=== AUTO MIGRATION DONE ==="
