import os
import time
import json
from werkzeug.utils import secure_filename
from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from app.models import db, Asset, Location
from app.routes import bp
from app.utils import login_required, permission_required

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def serialize_asset(asset):
    """Serialize data aset untuk kanvas layout editor in-app dan modal pop-up."""
    kondisi_lower = (asset.kondisi or 'baik').lower()
    if 'rusak berat' in kondisi_lower or (asset.skor_kerusakan and asset.skor_kerusakan >= 3):
        status_color = 'red'
        status_label = 'Rusak Berat'
    elif 'rusak' in kondisi_lower or 'perbaikan' in kondisi_lower or (asset.skor_kerusakan and asset.skor_kerusakan >= 2):
        status_color = 'amber'
        status_label = 'Maintenance / Rusak Ringan'
    else:
        status_color = 'green'
        status_label = 'Normal (Siap Pakai)'

    last_service = asset.perbaikan_list[0] if asset.perbaikan_list else None
    service_info = {
        'tanggal': last_service.tanggal_perbaikan.strftime('%d %b %Y'),
        'deskripsi': last_service.deskripsi,
        'biaya': f"Rp {int(last_service.biaya_perbaikan):,}".replace(',', '.')
    } if last_service else None

    foto_url = None
    if asset.foto_path:
        foto_url = url_for('static', filename=asset.foto_path)

    return {
        'id': asset.id,
        'nama_aset': asset.nama_aset,
        'kode_aset': asset.kode_aset,
        'format_label': asset.format_label(),
        'kategori': asset.category.nama_kategori if asset.category else '-',
        'lokasi': asset.location.nama_lab if asset.location else '-',
        'kondisi': asset.kondisi or 'Baik',
        'status_color': status_color,
        'status_label': status_label,
        'deskripsi': asset.deskripsi or 'Perangkat workstation komputer laboratorium praktikum.',
        'tahun_pengadaan': asset.tahun_pengadaan or '-',
        'sisa_umur': asset.sisa_umur_ekonomis(),
        'harga_perolehan': f"Rp {int(asset.harga_perolehan or 0):,}".replace(',', '.'),
        'nilai_buku': f"Rp {int(asset.nilai_buku()):,}".replace(',', '.'),
        'foto_url': foto_url,
        'detail_url': url_for('main.detail_asset', id=asset.id),
        'pos_x': round(asset.pos_x, 2) if asset.pos_x is not None else None,
        'pos_y': round(asset.pos_y, 2) if asset.pos_y is not None else None,
        'service_info': service_info
    }


def get_default_20_pc_template(location_id, assets):
    """Menghasilkan struktur template default 20 PC (sesuai sketsa Lab Basis Data)."""
    # Prioritaskan aset PC / Komputer untuk workstation PC-01 s.d. PC-20
    pc_assets = [a for a in assets if 'pc' in (a.nama_aset or '').lower() or 'komputer' in (a.nama_aset or '').lower()]
    bind_source = pc_assets if pc_assets else assets

    workstations = []
    rows = [
        (24.0, [('PC-01', 6.0), ('PC-02', 21.0), ('PC-03', 46.0), ('PC-04', 61.0), ('PC-05', 76.0)]),
        (42.0, [('PC-06', 6.0), ('PC-07', 21.0), ('PC-08', 46.0), ('PC-09', 61.0), ('PC-10', 76.0)]),
        (60.0, [('PC-11', 6.0), ('PC-12', 21.0), ('PC-13', 46.0), ('PC-14', 61.0), ('PC-15', 76.0)]),
        (78.0, [('PC-16', 6.0), ('PC-17', 21.0), ('PC-18', 46.0), ('PC-19', 61.0), ('PC-20', 76.0)])
    ]
    
    idx = 0
    for y, cols in rows:
        for label, x in cols:
            asset_id = bind_source[idx].id if idx < len(bind_source) else None
            workstations.append({
                'id': f'ws-{idx+1}',
                'label': label,
                'x': x,
                'y': y,
                'w': 12.5,
                'h': 12.0,
                'display_type': 'shape',
                'asset_id': asset_id
            })
            idx += 1
            
    fixtures = [
        {'id': 'door-1', 'type': 'door', 'label': 'PINTU', 'x': 5.5, 'y': 2.0, 'w': 13.0, 'h': 4.5},
        {'id': 'screen-1', 'type': 'projector', 'label': 'LAYAR PROYEKTOR', 'x': 34.0, 'y': 8.0, 'w': 18.0, 'h': 7.0},
        {'id': 'lecturer-1', 'type': 'lecturer', 'label': 'MEJA DOSEN', 'x': 54.0, 'y': 7.0, 'w': 33.0, 'h': 13.0},
        {'id': 'aisle-1', 'type': 'text', 'label': 'LORONG\nTENGAH', 'x': 35.0, 'y': 48.0, 'w': 8.5, 'h': 8.0},
        {'id': 'ac-1', 'type': 'ac', 'label': 'AC 1', 'x': 10.0, 'y': 94.5, 'w': 15.0, 'h': 4.0},
        {'id': 'ac-2', 'type': 'ac', 'label': 'AC 2', 'x': 67.0, 'y': 94.5, 'w': 15.0, 'h': 4.0}
    ]
    
    return {
        'room_title': 'LABORATORIUM KOMPUTER (20 PC)',
        'fixtures': fixtures,
        'workstations': workstations
    }


@bp.route('/floor-plan')
@permission_required('view_floor_plan')
def floor_plan():
    """Tampilan In-App Canvas / Grid Layout Editor Mandiri 2D Laboratorium.
    Administrator dapat mendesain tata letak ruangan, menambahkan elemen arsitektur,
    dan memetakan komputer PC-01 s.d. PC-20 secara visual tanpa ketergantungan gambar statis.
    """
    locations = Location.query.order_by(Location.id).all()
    selected_loc_id = request.args.get('location_id', type=int)

    # Pilih lokasi default (utamakan lab dengan aset terbanyak jika ada)
    if not selected_loc_id and locations:
        loc_with_assets = sorted(locations, key=lambda l: len(l.assets), reverse=True)
        selected_loc_id = loc_with_assets[0].id if loc_with_assets else locations[0].id

    current_location = Location.query.get(selected_loc_id) if selected_loc_id else None
    
    # Ambil seluruh aset di laboratorium terpilih
    all_lab_assets = Asset.query.filter_by(lokasi_id=selected_loc_id).order_by(Asset.id).all() if selected_loc_id else []

    # Ambil layout config tersimpan atau inisialisasi default jika kosong
    layout_data = None
    if current_location:
        if current_location.layout_config:
            try:
                layout_data = json.loads(current_location.layout_config)
            except Exception:
                layout_data = None
        
        # Jika belum ada konfigurasi layout, inisialisasi kanvas kosong mandiri (draw.io style)
        if not layout_data:
            layout_data = {
                'room_title': f"{current_location.nama_lab.upper()}",
                'fixtures': [],
                'workstations': []
            }
            current_location.layout_config = json.dumps(layout_data)
            db.session.commit()

    # Hitung metrik kondisi
    baik_count = sum(1 for a in all_lab_assets if (a.kondisi or 'Baik') == 'Baik' and (a.skor_kerusakan or 1) < 2)
    maint_count = sum(1 for a in all_lab_assets if (a.kondisi or '').startswith('Rusak Ringan') or (a.skor_kerusakan or 1) in [2, 3])
    rusak_berat_count = sum(1 for a in all_lab_assets if (a.kondisi or '') == 'Rusak Berat' or (a.skor_kerusakan or 1) >= 3)

    # Identifikasi aset yang sudah terikat ke meja (placed)
    placed_ids = set()
    if layout_data and 'workstations' in layout_data:
        for ws in layout_data['workstations']:
            if ws.get('asset_id'):
                placed_ids.add(ws['asset_id'])

    placed_count = len(placed_ids)
    unplaced_count = max(0, len(all_lab_assets) - placed_count)

    # Serialisasi semua aset lab untuk JavaScript
    assets_json = [serialize_asset(a) for a in all_lab_assets]

    return render_template('floor_plan.html',
        locations=locations,
        current_location=current_location,
        all_lab_assets=all_lab_assets,
        assets_json=json.dumps(assets_json),
        layout_json=json.dumps(layout_data) if layout_data else '{}',
        total_assets=len(all_lab_assets),
        placed_count=placed_count,
        unplaced_count=unplaced_count,
        baik_count=baik_count,
        maint_count=maint_count,
        rusak_berat_count=rusak_berat_count
    )


@bp.route('/api/floor-plan/save-layout', methods=['POST'])
@permission_required('view_floor_plan')
def save_floor_plan_layout():
    """Menyimpan seluruh konfigurasi layout in-app (fixtures & workstations) dan memperbarui koordinat aset di SQLite."""
    data = request.get_json()
    if not data or 'location_id' not in data or 'layout_config' not in data:
        return jsonify({'success': False, 'message': 'Data payload tidak lengkap'}), 400

    location_id = data.get('location_id')
    layout_config = data.get('layout_config')

    location = Location.query.get(location_id)
    if not location:
        return jsonify({'success': False, 'message': 'Laboratorium tidak ditemukan'}), 404

    try:
        # Simpan full layout config JSON ke tabel locations menggunakan method model
        location.save_layout(layout_config)

        # Sinkronisasi koordinat pos_x dan pos_y pada tabel assets
        placed_asset_ids = set()
        workstations = layout_config.get('workstations', [])

        for ws in workstations:
            asset_id = ws.get('asset_id')
            if asset_id:
                asset = Asset.query.get(asset_id)
                if asset and asset.lokasi_id == location_id:
                    asset.pos_x = float(ws.get('x', 0))
                    asset.pos_y = float(ws.get('y', 0))
                    placed_asset_ids.add(asset_id)

        # Aset lain di lab ini yang tidak terpasang di meja diset pos_x = None, pos_y = None
        for asset in Asset.query.filter_by(lokasi_id=location_id).all():
            if asset.id not in placed_asset_ids:
                asset.pos_x = None
                asset.pos_y = None

        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Konfigurasi denah ruangan ({len(workstations)} meja & {len(layout_config.get("fixtures", []))} objek ruangan) berhasil disimpan!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal menyimpan: {str(e)}'}), 500


@bp.route('/api/floor-plan/reset-template-20', methods=['POST'])
@permission_required('view_floor_plan')
def reset_template_20():
    """Mengembalikan denah ke konfigurasi standar 20 PC (sesuai sketsa Lab Basis Data)."""
    data = request.get_json() or {}
    location_id = data.get('location_id')

    location = Location.query.get(location_id) if location_id else None
    if not location:
        return jsonify({'success': False, 'message': 'Lokasi tidak ditemukan'}), 404

    all_assets = Asset.query.filter_by(lokasi_id=location_id).order_by(Asset.id).all()
    template_data = get_default_20_pc_template(location_id, all_assets)
    template_data['room_title'] = f"{location.nama_lab.upper()} (20 PC)"

    try:
        location.layout_config = json.dumps(template_data)
        
        # Sync pos_x, pos_y
        for ws in template_data['workstations']:
            if ws.get('asset_id'):
                a = Asset.query.get(ws['asset_id'])
                if a:
                    a.pos_x = ws['x']
                    a.pos_y = ws['y']

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Berhasil menerapkan template standar 20 PC!',
            'layout_config': template_data
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/floor-plan/upload-image', methods=['POST'])
@permission_required('view_floor_plan')
def upload_floor_plan_image():
    """Opsi sekunder: Mengunggah berkas gambar latar belakang denah (.png, .jpg, .svg)."""
    location_id = request.form.get('location_id', type=int)
    location = Location.query.get(location_id) if location_id else None

    if not location:
        flash('Laboratorium tidak ditemukan.', 'danger')
        return redirect(url_for('main.floor_plan'))

    if 'denah_file' not in request.files:
        flash('Tidak ada berkas yang dipilih.', 'warning')
        return redirect(url_for('main.floor_plan', location_id=location_id))

    file = request.files['denah_file']
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"denah_lab_{location_id}_{int(time.time())}.{ext}"
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'floor_plans')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))

        if location.denah_image:
            old_path = os.path.join(upload_folder, location.denah_image)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        location.denah_image = filename
        db.session.commit()
        flash('Latar belakang denah kustom berhasil disimpan!', 'success')
    else:
        flash('Format berkas tidak didukung.', 'danger')

    return redirect(url_for('main.floor_plan', location_id=location_id))


@bp.route('/floor-plan/remove-image', methods=['POST'])
@permission_required('view_floor_plan')
def remove_floor_plan_image():
    """Menghapus gambar latar belakang kustom."""
    location_id = request.form.get('location_id', type=int)
    location = Location.query.get(location_id) if location_id else None

    if location and location.denah_image:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'floor_plans')
        old_path = os.path.join(upload_folder, location.denah_image)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
        location.denah_image = None
        db.session.commit()
        flash('Latar belakang denah kustom dihapus.', 'info')

    return redirect(url_for('main.floor_plan', location_id=location_id))
