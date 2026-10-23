import os
from functools import wraps
from flask import session, redirect, url_for, abort, current_app
import qrcode

def login_required(f):
    """Decorator: pastikan user sudah login (apapun rolenya).

    - Belum login → redirect ke halaman login (/login)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator: pastikan user sudah login DAN memiliki role 'admin'/'Super Admin' atau hak kelola pengguna."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        user_role = session.get('role', '')
        user_perms = session.get('permissions', [])
        if user_role in ['admin', 'Super Admin'] or 'all' in user_perms or 'manage_users' in user_perms:
            return f(*args, **kwargs)
        abort(403)
    return decorated_function


def permission_required(perm):
    """Decorator untuk mengecek apakah user yang sedang login memiliki hak permisi spesifik."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('main.login'))
            user_perms = session.get('permissions', [])
            user_role = session.get('role', '')
            if user_role in ['admin', 'Super Admin'] or 'all' in user_perms or perm in user_perms:
                return f(*args, **kwargs)
            from flask import flash
            flash('Akses Ditolak: Anda tidak memiliki hak akses untuk fitur tersebut.')
            return redirect(url_for('main.dashboard'))
        return decorated_function
    return decorator


def init_db_schema(app):
    """Memeriksa dan memperbarui skema database SQLite jika terdapat kolom baru."""
    from app import db
    from sqlalchemy import inspect, text

    with app.app_context():
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('users')]
            with db.engine.connect() as conn:
                if 'nama_lengkap' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN nama_lengkap VARCHAR(100)"))
                if 'jabatan' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN jabatan VARCHAR(100)"))
                if 'permissions' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN permissions TEXT"))
                conn.commit()

        if 'assets' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('assets')]
            with db.engine.connect() as conn:
                if 'foto_path' not in columns:
                    conn.execute(text("ALTER TABLE assets ADD COLUMN foto_path VARCHAR(255)"))
                conn.commit()


def generate_asset_qr(asset):
    """Membentuk teks QR Code lengkap (Nama, Kode, Lokasi, Deskripsi, Log Perbaikan)
    dan meregenerasi berkas gambar asset_<id>.png di static/qrcodes/.
    """
    nama = asset.nama_aset or "-"
    kode = asset.kode_aset or "-"
    lokasi = asset.location.nama_lab if asset.location else "-"
    deskripsi = asset.deskripsi if asset.deskripsi else "-"
    
    # Format Log Perbaikan
    perbaikan_count = len(asset.perbaikan_list) if asset.perbaikan_list else 0
    total_biaya = asset.biaya_perawatan or 0.0
    if perbaikan_count == 0:
        log_str = "Belum ada riwayat perbaikan"
    else:
        log_str = f"{perbaikan_count}x perbaikan (Total: Rp {total_biaya:,.0f})"
    
    qr_content = (
        f"Nama Aset: {nama}\n"
        f"Kode Aset: {kode}\n"
        f"Lokasi: {lokasi}\n"
        f"Deskripsi: {deskripsi}\n"
        f"Log Perbaikan: {log_str}"
    )
    
    qr = qrcode.make(qr_content)
    qr_filename = f"asset_{asset.id}.png"
    qr_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, qr_filename)
    qr.save(qr_path)
    
    asset.qr_code_path = f"qrcodes/{qr_filename}"
    return asset.qr_code_path
