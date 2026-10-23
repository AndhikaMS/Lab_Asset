from flask import render_template, session
from app.models import db, Asset, Location, PerbaikanAset, Category
from app.routes import bp
from app.routes.spk import hitung_saw, _get_bobot
from app.utils import login_required
from datetime import datetime
import json

@bp.route('/')
@login_required
def dashboard():
    # ─────────────────────────────────────────────────────────────────────────
    # 1. KPI Finansial & Operasional (Executive View)
    # ─────────────────────────────────────────────────────────────────────────
    semua_aset = Asset.query.all()
    total_assets = len(semua_aset)
    total_labs = Location.query.count()
    
    # --- Tambahan Data Master Dekan ---
    from app.models import Prodi, Category
    total_categories = Category.query.count()
    total_prodi = Prodi.query.count()

    total_investasi = sum(a.harga_perolehan or 0 for a in semua_aset)
    total_residu = sum(a.nilai_residu or 0 for a in semua_aset)
    total_nilai_buku = sum(a.nilai_buku() for a in semua_aset)
    avg_useful_life = round(sum(a.umur_ekonomis or 0 for a in semua_aset) / total_assets, 1) if total_assets > 0 else 0.0
    
    # Hitung total biaya perawatan historis dari tabel PerbaikanAset
    total_biaya_perawatan = db.session.query(db.func.sum(PerbaikanAset.biaya_perbaikan)).scalar() or 0.0

    # Kesehatan & Peringatan Usia Aset (Overdue / Melampaui Umur Ekonomis)
    overdue_assets = sum(1 for a in semua_aset if a.sisa_umur_ekonomis() == 0)
    
    # Metrik Kesiapan Lab
    aset_kondisi_baik = sum(1 for a in semua_aset if a.kondisi == 'Baik')
    persentase_baik = (aset_kondisi_baik / total_assets * 100) if total_assets > 0 else 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Top 5 Prioritas Penggantian (Live SPK SAW) & Aset Terbaru
    # ─────────────────────────────────────────────────────────────────────────
    bobot_default = _get_bobot(None)
    hasil_spk_lengkap = bobot_default.hitung_prioritas(semua_aset)
    top_5_spk = hasil_spk_lengkap[:5]
    recent_assets = Asset.query.order_by(Asset.id.desc()).limit(5).all()
    
    aset_rusak_berat = sum(1 for a in semua_aset if a.kondisi == 'Rusak Berat')

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Log Aktivitas Perbaikan Terbaru (Recent Activity Feed)
    # ─────────────────────────────────────────────────────────────────────────
    recent_perbaikan = PerbaikanAset.query.order_by(PerbaikanAset.tanggal_perbaikan.desc(), PerbaikanAset.id.desc()).limit(5).all()

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Data untuk Visualisasi Chart
    # ─────────────────────────────────────────────────────────────────────────
    # Chart 1: Distribusi Aset per Kategori (Doughnut count & value)
    categories = Category.query.order_by(Category.nama_kategori).all()
    kategori_labels = []
    kategori_counts = []
    kategori_values = []
    for cat in categories:
        cat_assets = Asset.query.filter_by(kategori_id=cat.id).all()
        cnt = len(cat_assets)
        if cnt > 0:
            kategori_labels.append(cat.nama_kategori)
            kategori_counts.append(cnt)
            kategori_values.append(sum(a.harga_perolehan or 0 for a in cat_assets))

    # Chart 2: Distribusi Aset per Lab (Bar)
    locations = Location.query.order_by(Location.nama_lab).all()
    lab_labels = []
    lab_counts = []
    for loc in locations:
        cnt = Asset.query.filter_by(lokasi_id=loc.id).count()
        if cnt > 0:
            lab_labels.append(loc.kode_lab or loc.nama_lab)
            lab_counts.append(cnt)

    return render_template('dashboard.html',
        # KPIs
        total_assets=total_assets,
        total_labs=total_labs,
        total_categories=total_categories,
        total_prodi=total_prodi,
        total_investasi=total_investasi,
        total_residu=total_residu,
        total_nilai_buku=total_nilai_buku,
        avg_useful_life=avg_useful_life,
        total_biaya_perawatan=total_biaya_perawatan,
        overdue_assets=overdue_assets,
        persentase_baik=persentase_baik,
        
        # SPK & Recent Assets
        top_5_spk=top_5_spk,
        recent_assets=recent_assets,
        aset_rusak_berat=aset_rusak_berat,
        
        # Chart Data
        kategori_labels=json.dumps(kategori_labels),
        kategori_counts=json.dumps(kategori_counts),
        kategori_values=json.dumps(kategori_values),
        lab_labels=json.dumps(lab_labels),
        lab_counts=json.dumps(lab_counts),

        # Recent Activity
        recent_perbaikan=recent_perbaikan,
    )
