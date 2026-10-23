import os
import sqlite3
import qrcode
from flask import Response, request, redirect, url_for, flash, current_app
from app.models import db, Asset
from app.routes import bp
from app.utils import admin_required

@bp.route('/backup-db')
@admin_required
def backup_db():
    try:
        db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.join(current_app.root_path, '..', 'app.db')
        
        con = sqlite3.connect(db_path)
        sql_lines = []
        for line in con.iterdump():
            sql_lines.append(f"{line}\n")
        con.close()
        
        sql_data = "".join(sql_lines)
        return Response(
            sql_data,
            mimetype='application/sql',
            headers={
                'Content-Disposition': 'attachment; filename=backup_app.sql'
            }
        )
    except Exception as e:
        flash(f'Gagal melakukan backup database: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@bp.route('/restore-db', methods=['POST'])
@admin_required
def restore_db():
    if 'backup_file' not in request.files:
        flash('Tidak ada berkas SQL yang diunggah.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    file = request.files['backup_file']
    if file.filename == '':
        flash('Silakan pilih berkas backup_app.sql terlebih dahulu.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if not file.filename.endswith('.sql'):
        flash('Format berkas harus berupa .sql', 'danger')
        return redirect(url_for('main.dashboard'))

    try:
        sql_script = file.read().decode('utf-8')
        db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.join(current_app.root_path, '..', 'app.db')
        
        # Release SQLAlchemy session
        db.session.remove()

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys = OFF;")
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        for t in tables:
            if t[0] != 'sqlite_sequence':
                cur.execute(f"DROP TABLE IF EXISTS [{t[0]}];")
        con.commit()
        
        con.executescript(sql_script)
        con.close()

        # Regenerate QR Codes for all restored assets
        static_qr = os.path.join(current_app.root_path, 'static', 'qrcodes')
        os.makedirs(static_qr, exist_ok=True)

        assets = Asset.query.all()
        qr_count = 0
        for a in assets:
            final_deskripsi = a.deskripsi if a.deskripsi else "-"
            qr_content = f"Kode Aset : {a.kode_aset}\nNama Aset : {a.nama_aset}\nDeskripsi Aset : {final_deskripsi}"
            qr = qrcode.make(qr_content)
            
            qr_filename = f"asset_{a.id}.png"
            qr_path = os.path.join(static_qr, qr_filename)
            qr.save(qr_path)
            
            a.qr_code_path = f"qrcodes/{qr_filename}"
            qr_count += 1
            
        db.session.commit()

        # Also write to local backup_app.sql
        with open('backup_app.sql', 'w', encoding='utf-8') as f:
            f.write(sql_script)

        flash(f'Pangkalan data dan {qr_count} berkas QR Code berhasil dipulihkan!', 'success')
    except Exception as e:
        flash(f'Gagal memulihkan database: {str(e)}', 'danger')

    return redirect(url_for('main.dashboard'))
