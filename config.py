import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Memuat file .env jika tersedia
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Mengambil konfigurasi dari environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Validasi: Jika pengguna clone dari GitHub tanpa membuat .env, aplikasi sengaja dibuat tidak berjalan
    if not SECRET_KEY or not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "\n[CONFIG ERROR] Aplikasi tidak dapat dijalankan!\n"
            "File konfigurasi (.env) belum disiapkan.\n"
            "Langkah perbaikan:\n"
            "  1. Salin file '.env.example' menjadi '.env'\n"
            "  2. Isi nilai SECRET_KEY dan DATABASE_URL (misal: DATABASE_URL=sqlite:///app.db)\n"
            "  3. Jalankan kembali aplikasi."
        )

