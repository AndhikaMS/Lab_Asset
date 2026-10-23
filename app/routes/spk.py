from flask import render_template, request, redirect, url_for, flash
from app.models import db, Asset, BobotSAW, Category, KepalaLab, Location
from app.routes import bp
from app.utils import permission_required, admin_required
from datetime import datetime


def hitung_saw(assets, bobot):
    """
    Menghitung Simple Additive Weighting (SAW) untuk ranking penggantian aset.

    Kriteria:
    - C1: Persentase Sisa Umur Ekonomis (cost — semakin kecil, semakin kritis)
           Rumus: sisa_umur / umur_ekonomis
           Nilai 0 = umur habis (paling kritis), Nilai 1 = masih baru.
           Normalisasi cost SAW: R = min_C1 / nilai_C1
    - C2: Skor kerusakan fisik (benefit — semakin besar, semakin kritis)
    - C3: Biaya perawatan historis (benefit — semakin besar, semakin kritis)

    Returns list of dicts: [{asset, c1, c2, c3, skor_akhir}]
    """
    if not assets:
        return []

    # Kumpulkan nilai mentah
    data = []
    for asset in assets:
        # C1: Persentase Sisa Umur Ekonomis (cost criterion)
        # sisa_umur / umur_ekonomis  →  0 = habis (kritis), 1 = masih baru
        if asset.umur_ekonomis and asset.umur_ekonomis > 0 and asset.tahun_pengadaan:
            sisa = asset.sisa_umur_ekonomis()
            c1 = round(sisa / asset.umur_ekonomis, 6)
        else:
            # Tidak ada data umur → anggap sudah habis (paling kritis)
            c1 = 0.0

        c2 = float(asset.skor_kerusakan or 1)
        c3 = float(asset.biaya_perawatan or 0)
        data.append({'asset': asset, 'c1': c1, 'c2': c2, 'c3': c3})

    # Nilai untuk normalisasi
    min_c1 = min(d['c1'] for d in data)   # cost: pakai min
    max_c2 = max(d['c2'] for d in data)   # benefit: pakai max
    max_c3 = max(d['c3'] for d in data)   # benefit: pakai max

    results = []
    for d in data:
        asset = d['asset']

        # Normalisasi C1 (cost): R = min / nilai
        # Jika nilai = 0 (umur habis) → R = 1.0 (paling kritis)
        if d['c1'] > 0:
            r_c1 = min_c1 / d['c1'] if min_c1 > 0 else 1.0
        else:
            r_c1 = 1.0  # umur habis = nilai normalisasi tertinggi (paling kritis)

        # Normalisasi C2 (benefit): R = nilai / max
        r_c2 = d['c2'] / max_c2 if max_c2 > 0 else 0.0

        # Normalisasi C3 (benefit): R = nilai / max
        r_c3 = d['c3'] / max_c3 if max_c3 > 0 else 0.0

        # Skor akhir
        skor = (bobot.bobot_c1 * r_c1) + (bobot.bobot_c2 * r_c2) + (bobot.bobot_c3 * r_c3)

        results.append({
            'asset':      asset,
            'c1_raw':     d['c1'],
            'c2_raw':     d['c2'],
            'c3_raw':     d['c3'],
            'r_c1':       round(r_c1, 4),
            'r_c2':       round(r_c2, 4),
            'r_c3':       round(r_c3, 4),
            'skor_akhir': round(skor, 4),
        })

    # Urutkan dari skor tertinggi (paling kritis)
    results.sort(key=lambda x: x['skor_akhir'], reverse=True)
    return results


def _get_bobot(kategori_id=None):
    """Ambil bobot untuk kategori tertentu; fallback ke bobot default (NULL)."""
    if kategori_id:
        bobot = BobotSAW.query.filter_by(kategori_id=kategori_id).first()
        if bobot:
            return bobot
    # Fallback: bobot default
    bobot = BobotSAW.query.filter_by(kategori_id=None).first()
    if not bobot:
        bobot = BobotSAW(kategori_id=None, bobot_c1=0.4, bobot_c2=0.35, bobot_c3=0.25)
        db.session.add(bobot)
        db.session.commit()
    return bobot


@bp.route('/spk')
@permission_required('view_spk')
def spk():
    """Halaman utama SPK — menampilkan ranking penggantian aset per kategori."""
    categories = Category.query.order_by(Category.nama_kategori).all()
    locations = Location.query.order_by(Location.nama_lab).all()

    # Kategori dan Lokasi yang dipilih
    kat_id = request.args.get('kategori_id', type=int)
    loc_id = request.args.get('location_id', type=int)

    # Ambil bobot yang sesuai
    bobot = _get_bobot(kat_id)

    # Filter aset berdasarkan kategori dan lokasi
    query = Asset.query
    if kat_id:
        query = query.filter_by(kategori_id=kat_id)
    if loc_id:
        query = query.filter_by(lokasi_id=loc_id)
    
    assets = query.all()
    ranking = bobot.hitung_prioritas(assets)

    # Daftar semua bobot yang sudah dikustomisasi per-kategori (untuk ditampilkan)
    bobot_per_kat = {b.kategori_id: b for b in BobotSAW.query.all()}

    return render_template('spk.html',
        ranking=ranking,
        bobot=bobot,
        categories=categories,
        locations=locations,
        selected_kat_id=kat_id,
        selected_loc_id=loc_id,
        bobot_per_kat=bobot_per_kat,
    )


@bp.route('/spk/bobot', methods=['POST'])
@permission_required('edit_spk_bobot')
def spk_update_bobot():
    """Simpan/update bobot kriteria SAW untuk kategori tertentu (atau default)."""
    kat_id = request.form.get('kategori_id', type=int)  # None = default

    b1 = float(request.form.get('bobot_c1', 0.4))
    b2 = float(request.form.get('bobot_c2', 0.35))
    b3 = float(request.form.get('bobot_c3', 0.25))

    total = b1 + b2 + b3
    if abs(total - 1.0) > 0.001:
        flash(f'Total bobot harus 1.0. Saat ini total = {total:.3f}', 'error')
        return redirect(url_for('main.spk', kategori_id=kat_id or ''))

    # Cari atau buat record bobot untuk kategori ini
    bobot = BobotSAW.query.filter_by(kategori_id=kat_id).first()
    if not bobot:
        bobot = BobotSAW(kategori_id=kat_id)
        bobot.insert_data()

    bobot.update_bobot(b1, b2, b3)

    flash('Bobot berhasil diupdate!', 'success')
    return redirect(url_for('main.spk', kategori_id=kat_id or ''))


@bp.route('/spk/bobot/reset', methods=['POST'])
@permission_required('edit_spk_bobot')
def spk_reset_bobot():
    """Hapus bobot khusus kategori, kembalikan ke default."""
    kat_id = request.form.get('kategori_id', type=int)
    if kat_id:
        bobot = BobotSAW.query.filter_by(kategori_id=kat_id).first()
        if bobot:
            db.session.delete(bobot)
            db.session.commit()
            flash('Bobot kategori direset ke default.')
    return redirect(url_for('main.spk', kategori_id=kat_id or ''))


@bp.route('/spk/print')
@permission_required('print_reports')
def spk_print():
    """Laporan cetak formal hasil SPK."""
    kat_id = request.args.get('kategori_id', type=int)
    bobot  = _get_bobot(kat_id)

    if kat_id:
        assets = Asset.query.filter_by(kategori_id=kat_id).all()
    else:
        assets = Asset.query.all()

    ranking = hitung_saw(assets, bobot)

    kepala_lab = KepalaLab.query.filter_by(is_active=True).first()
    if not kepala_lab:
        kepala_lab = KepalaLab.query.order_by(KepalaLab.id.desc()).first()

    kat_nama = Category.query.get(kat_id).nama_kategori if kat_id else 'Semua Kategori'

    return render_template('spk_print.html',
        ranking=ranking,
        bobot=bobot,
        kepala_lab=kepala_lab,
        date=datetime.now(),
        kat_nama=kat_nama,
    )
