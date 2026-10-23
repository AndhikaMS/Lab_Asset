from flask import render_template, request
from app.models import Asset, Location, KepalaLab, Category
from app.routes import bp
from app.utils import permission_required
from datetime import datetime

@bp.route('/print/label/<int:asset_id>')
@permission_required('print_reports')
def print_label(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    
    kode_lokasi = asset.format_kode_lokasi()
    kode_barang = asset.format_kode_barang()
    
    return render_template('print_label.html', asset=asset, kode_lokasi=kode_lokasi, kode_barang=kode_barang)

@bp.route('/print/inventory')
@permission_required('print_reports')
def print_inventory_select():
    # Page to select which lab to print
    locations = Location.query.all()
    return render_template('print_select.html', locations=locations)

@bp.route('/print/inventory/<int:location_id>')
@permission_required('print_reports')
def print_inventory(location_id):
    location = Location.query.get_or_404(location_id)
    # Sort by Category Name Ascending, then by Asset Code Ascending (as proxy for Nomor Urut)
    assets = Asset.query.filter_by(lokasi_id=location_id)\
        .join(Category)\
        .order_by(Category.nama_kategori.asc(), Asset.kode_aset.asc())\
        .all()
    # Fetch the active Kepala Lab for signature
    kepala_lab = KepalaLab.query.filter_by(is_active=True).first()
    # Fallback to latest if no one is explicitly marked active
    if not kepala_lab:
        kepala_lab = KepalaLab.query.order_by(KepalaLab.id.desc()).first()
    return render_template('print_inventory.html', location=location, assets=assets, date=datetime.now(), kepala_lab=kepala_lab)

@bp.route('/print/labels-all')
@permission_required('print_reports')
def print_all_labels():
    loc_id = request.args.get('location')
    cat_id = request.args.get('category')
    selected_ids = request.args.get('selected_ids')
    
    query = Asset.query
    ids = []
    if selected_ids:
        try:
            ids = [int(i.strip()) for i in selected_ids.split(',') if i.strip().isdigit()]
            if ids:
                query = query.filter(Asset.id.in_(ids))
        except Exception:
            pass
    else:
        if loc_id:
            query = query.filter_by(lokasi_id=loc_id)
        if cat_id:
            query = query.filter_by(kategori_id=cat_id)
        
    assets_data = query.order_by(Asset.id.asc()).all()
    
    # Pertahankan urutan ID yang dipilih pengguna jika ada
    if selected_ids and ids:
        id_map = {a.id: a for a in assets_data}
        assets_data = [id_map[i] for i in ids if i in id_map]
    
    # Prepare labels data
    labels = []
    for asset in assets_data:
        labels.append({
            'asset': asset,
            'kode_lokasi': asset.format_kode_lokasi(),
            'kode_barang': asset.format_kode_barang()
        })
        
    return render_template('print_all_labels.html', labels=labels)

