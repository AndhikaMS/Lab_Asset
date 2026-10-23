from flask import render_template, request, redirect, url_for, flash, current_app
from app.models import db, Asset, Location, Category, Prodi, KodeLokasi, KodeBarang
from app.routes import bp
from app.utils import permission_required
import qrcode
import os

@bp.route('/assets/create', methods=['GET', 'POST'])
@permission_required('edit_assets')
def create_asset():
    if request.method == 'POST':
        nama_aset = request.form['nama_aset']
        kategori_id = request.form['kategori_id']
        prodi_id = request.form['prodi_id']
        lokasi_id = request.form['lokasi_id']
        deskripsi = request.form['deskripsi']
        
        # Data Ekonomis
        harga_perolehan = float(request.form.get('harga_perolehan', 0) or 0)
        umur_ekonomis = int(request.form.get('umur_ekonomis', 5) or 5)
        nilai_residu = float(request.form.get('nilai_residu', 0) or 0)
        skor_kerusakan = int(request.form.get('skor_kerusakan', 1) or 1)
        # Biaya perawatan otomatis 0 saat registrasi aset baru (dikendalikan dari menu Riwayat Perbaikan)
        biaya_perawatan = 0.0
        
        # Mapping Kondisi otomatis berdasarkan Skor Kerusakan Fisik (C2 SPK skala 1-3)
        if skor_kerusakan == 1:
            kondisi = 'Baik'
        elif skor_kerusakan == 2:
            kondisi = 'Rusak Ringan'
        else:
            kondisi = 'Rusak Berat'
        
        # New Codification Inputs
        c_yayasan = request.form['code_yayasan'] # 4
        c_rektorat = request.form['code_rektorat'] # 2
        c_fakultas = request.form['code_fakultas'] # 2
        
        # Get Prodi Code Component
        prodi = Prodi.query.get(prodi_id)
        c_prodi = prodi.kode_aset # Use kode_aset from master data
        c_lokasi = request.form['code_lokasi'] # 2
        
        c_gol = request.form['code_golongan'] # 2
        c_bid = request.form['code_bidang'] # 2
        c_kel = request.form['code_kelompok'] # 2
        c_sub = request.form['code_subkel'] # 2
        c_tahun = request.form['code_tahun'] # 4
        c_urut_lok = request.form['code_urutan_lok'] # 1
        c_no_urut = request.form['code_nomor_urut'] # 2
        
        # Construct Final Code
        final_code = f"{c_yayasan} {c_rektorat} {c_fakultas} {c_prodi} {c_lokasi} {c_gol} {c_bid} {c_kel} {c_sub} {c_tahun} {c_urut_lok}{c_no_urut}"
        
        # 1. Create KodeLokasi
        new_kl = KodeLokasi(
            yayasan=c_yayasan,
            rektorat=c_rektorat,
            fakultas=c_fakultas,
            prodi_id=prodi_id,
            ruangan=c_lokasi
        )
        db.session.add(new_kl)
        db.session.flush()

        # 2. Create KodeBarang
        loc_for_urut = Location.query.filter_by(kode_aset=c_urut_lok).first()
        l_id_urut = loc_for_urut.id if loc_for_urut else None

        new_kb = KodeBarang(
            golongan=c_gol,
            bidang=c_bid,
            kelompok=c_kel,
            subkelompok=c_sub,
            tahun_pengadaan=c_tahun,
            urutan_ruangan_id=l_id_urut,
            nomor_urut=c_no_urut
        )
        db.session.add(new_kb)
        db.session.flush()

        # 3. Create Asset
        new_asset = Asset(
            kode_aset=final_code, 
            nama_aset=nama_aset,
            kategori_id=kategori_id,
            lokasi_id=lokasi_id,
            prodi_id=prodi_id,
            kode_lokasi_id=new_kl.id,
            kode_barang_id=new_kb.id,
            deskripsi=deskripsi,
            kondisi=kondisi,
            tahun_pengadaan=int(c_tahun),
            harga_perolehan=harga_perolehan,
            umur_ekonomis=umur_ekonomis,
            nilai_residu=nilai_residu,
            skor_kerusakan=skor_kerusakan,
            biaya_perawatan=biaya_perawatan
        )
        new_asset.insert_data()

        # Handle Upload Foto Aset
        foto_file = request.files.get('foto_barang')
        if foto_file and foto_file.filename != '':
            ext = os.path.splitext(foto_file.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                import uuid
                filename = f"asset_{new_asset.id}_{uuid.uuid4().hex[:8]}{ext}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'assets')
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, filename)
                foto_file.save(save_path)
                new_asset.foto_path = f"uploads/assets/{filename}"
                db.session.commit()
        
        from app.utils import generate_asset_qr
        generate_asset_qr(new_asset)
        db.session.commit()
        
        flash(f'Asset created successfully. Code: {final_code}')
        return redirect(url_for('main.assets'))
        
    locations = Location.query.all()
    categories = Category.query.all()
    prodis = Prodi.query.all()
    return render_template('asset_form.html', locations=locations, categories=categories, prodis=prodis)
