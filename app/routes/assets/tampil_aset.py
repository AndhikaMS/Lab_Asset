from flask import render_template, request
from app.models import db, Asset, Location, Category, Prodi
from app.routes import bp
from app.utils import permission_required

@bp.route('/assets', methods=['GET'])
@permission_required('view_assets')
def assets():
    # Ambil Parameter Filter
    loc_id = request.args.get('location', type=int)
    cat_id = request.args.get('category', type=int)
    prodi_id = request.args.get('prodi', type=int)
    kondisi = request.args.get('kondisi', '').strip()
    tahun = request.args.get('tahun', type=int)
    search_q = request.args.get('q', '').strip()
    
    query = Asset.query
    if loc_id:
        query = query.filter_by(lokasi_id=loc_id)
    if cat_id:
        query = query.filter_by(kategori_id=cat_id)
    if prodi_id:
        query = query.filter_by(prodi_id=prodi_id)
    if kondisi:
        query = query.filter_by(kondisi=kondisi)
    if tahun:
        query = query.filter_by(tahun_pengadaan=tahun)
    if search_q:
        search_term = f"%{search_q}%"
        query = query.filter(
            (Asset.nama_aset.ilike(search_term)) |
            (Asset.kode_aset.ilike(search_term)) |
            (Asset.deskripsi.ilike(search_term))
        )
        
    total_found = query.count()
    total_all = Asset.query.count()
    all_assets = query.order_by(Asset.id.desc()).all()
    
    locations = Location.query.order_by(Location.nama_lab).all()
    categories = Category.query.order_by(Category.nama_kategori).all()
    prodis = Prodi.query.order_by(Prodi.nama_prodi).all()
    
    # Ambil daftar tahun pengadaan unik
    years_tuples = db.session.query(Asset.tahun_pengadaan).distinct().filter(Asset.tahun_pengadaan.isnot(None)).order_by(Asset.tahun_pengadaan.desc()).all()
    available_years = [y[0] for y in years_tuples if y[0]]
    
    return render_template(
        'assets.html',
        assets=all_assets,
        locations=locations,
        categories=categories,
        prodis=prodis,
        available_years=available_years,
        total_found=total_found,
        total_all=total_all
    )
