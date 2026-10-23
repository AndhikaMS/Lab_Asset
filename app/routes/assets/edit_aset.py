from flask import render_template, request, redirect, url_for, flash, current_app
from app.models import db, Asset, Location, Category, Prodi, KodeLokasi, KodeBarang
from app.routes import bp
from app.utils import permission_required
import qrcode
import os

@bp.route('/assets/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('edit_assets')
def edit_asset(id):
    asset = Asset.query.get_or_404(id)
    if request.method == 'POST':
        # New Codification Inputs
        c_yayasan = request.form['code_yayasan'] 
        c_rektorat = request.form['code_rektorat'] 
        c_fakultas = request.form['code_fakultas'] 
        
        # Prodi Logic
        prodi_id = request.form['prodi_id']
        prodi = Prodi.query.get(prodi_id)
        c_prodi = prodi.kode_aset # Use kode_aset from master data
        
        c_lokasi = request.form['code_lokasi'] 
        
        c_gol = request.form['code_golongan'] 
        c_bid = request.form['code_bidang'] 
        c_kel = request.form['code_kelompok'] 
        c_sub = request.form['code_subkel'] 
        c_tahun = request.form['code_tahun'] 
        c_urut_lok = request.form['code_urutan_lok'] 
        c_no_urut = request.form['code_nomor_urut']
        
        # Construct Final Code
        final_code = f"{c_yayasan} {c_rektorat} {c_fakultas} {c_prodi} {c_lokasi} {c_gol} {c_bid} {c_kel} {c_sub} {c_tahun} {c_urut_lok}{c_no_urut}"

        # Update or Create KodeLokasi
        if not asset.kode_lokasi:
            kl = KodeLokasi()
            db.session.add(kl)
            asset.kode_lokasi = kl
        
        asset.kode_lokasi.yayasan = c_yayasan
        asset.kode_lokasi.rektorat = c_rektorat
        asset.kode_lokasi.fakultas = c_fakultas
        asset.kode_lokasi.prodi_id = prodi_id
        asset.kode_lokasi.ruangan = c_lokasi
        
        # Update or Create KodeBarang
        if not asset.kode_barang:
            kb = KodeBarang()
            db.session.add(kb)
            asset.kode_barang = kb
            
        loc_for_urut = Location.query.filter_by(kode_aset=c_urut_lok).first()
        asset.kode_barang.golongan = c_gol
        asset.kode_barang.bidang = c_bid
        asset.kode_barang.kelompok = c_kel
        asset.kode_barang.subkelompok = c_sub
        asset.kode_barang.tahun_pengadaan = c_tahun
        asset.kode_barang.urutan_ruangan_id = loc_for_urut.id if loc_for_urut else None
        asset.kode_barang.nomor_urut = c_no_urut

        asset.kode_aset = final_code
        asset.nama_aset = request.form['nama_aset']
        asset.kategori_id = request.form['kategori_id']
        asset.prodi_id = prodi_id
        asset.lokasi_id = request.form['lokasi_id']
        asset.deskripsi = request.form['deskripsi']
        asset.tahun_pengadaan = int(c_tahun)
        
        # Data Ekonomis & SPK
        asset.harga_perolehan = float(request.form.get('harga_perolehan', 0) or 0)
        asset.umur_ekonomis = int(request.form.get('umur_ekonomis', 5) or 5)
        asset.nilai_residu = float(request.form.get('nilai_residu', 0) or 0)
        asset.skor_kerusakan = int(request.form.get('skor_kerusakan', 1) or 1)
        # asset.biaya_perawatan dikendalikan otomatis dari modul Riwayat Perbaikan (/perbaikan)
        
        # Mapping Kondisi otomatis berdasarkan Skor Kerusakan Fisik (C2 SPK skala 1-3)
        if asset.skor_kerusakan == 1:
            asset.kondisi = 'Baik'
        elif asset.skor_kerusakan == 2:
            asset.kondisi = 'Rusak Ringan'
        else:
            asset.kondisi = 'Rusak Berat'
        
        # Handle Upload Foto Aset Baru
        foto_file = request.files.get('foto_barang')
        if foto_file and foto_file.filename != '':
            ext = os.path.splitext(foto_file.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                import uuid
                filename = f"asset_{asset.id}_{uuid.uuid4().hex[:8]}{ext}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'assets')
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, filename)
                foto_file.save(save_path)
                asset.foto_path = f"uploads/assets/{filename}"

        from app.utils import generate_asset_qr
        generate_asset_qr(asset)
        
        db.session.commit()
        flash('Asset updated successfully')
        return redirect(url_for('main.assets'))
    
    locations = Location.query.all()
    categories = Category.query.all()
    prodis = Prodi.query.all()
    
    # Pre-fill form from separate tables
    components = {}
    if asset.kode_lokasi:
        kl = asset.kode_lokasi
        components.update({
            'yayasan': kl.yayasan,
            'rektorat': kl.rektorat,
            'fakultas': kl.fakultas,
            'prodi': kl.prodi.kode_aset if kl.prodi else '',
            'lokasi': kl.ruangan
        })
    
    if asset.kode_barang:
        kb = asset.kode_barang
        components.update({
            'golongan': kb.golongan,
            'bidang': kb.bidang,
            'kelompok': kb.kelompok,
            'subkel': kb.subkelompok,
            'tahun': kb.tahun_pengadaan,
            'urutan_lok': kb.location.kode_aset if kb.location else '',
            'nomor_urut': kb.nomor_urut
        })
    elif asset.kode_aset:
        # Fallback to parsing if tables are empty
        try:
            parts = asset.kode_aset.split(' ')
            if len(parts) >= 11:
                components = {
                    'yayasan': parts[0],
                    'rektorat': parts[1],
                    'fakultas': parts[2],
                    'prodi': parts[3],
                    'lokasi': parts[4],
                    'golongan': parts[5],
                    'bidang': parts[6],
                    'kelompok': parts[7],
                    'subkel': parts[8],
                    'tahun': parts[9],
                    'urutan_lok': parts[10][0] if len(parts[10]) > 0 else '',
                    'nomor_urut': parts[10][1:] if len(parts[10]) > 1 else ''
                }
        except Exception as e:
            print(f"Error parsing code: {e}")

    return render_template('edit_asset.html', asset=asset, locations=locations, categories=categories, prodis=prodis, components=components)
