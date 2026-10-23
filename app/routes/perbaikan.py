from flask import render_template, request, redirect, url_for, flash
from app.models import db, PerbaikanAset, Asset
from app.routes import bp
from app.utils import permission_required, admin_required
from datetime import datetime, date


def _recalculate_biaya(asset):
    """Hitung ulang biaya_perawatan aset dari total semua record perbaikan-nya dan update QR Code."""
    total = db.session.query(
        db.func.sum(PerbaikanAset.biaya_perbaikan)
    ).filter_by(asset_id=asset.id).scalar() or 0.0
    asset.biaya_perawatan = total
    from app.utils import generate_asset_qr
    generate_asset_qr(asset)
    db.session.commit()


# ── LIST ──────────────────────────────────────────────────────────────────────
@bp.route('/perbaikan')
@permission_required('view_perbaikan')
def perbaikan():
    # Filter opsional berdasarkan aset
    asset_id = request.args.get('asset_id', type=int)
    query = PerbaikanAset.query.order_by(PerbaikanAset.tanggal_perbaikan.desc())
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    semua_perbaikan = query.all()
    semua_aset = Asset.query.order_by(Asset.nama_aset).all()
    return render_template('perbaikan.html',
                           perbaikan_list=semua_perbaikan,
                           semua_aset=semua_aset,
                           filter_asset_id=asset_id,
                           today=date.today().isoformat())


# ── ADD ───────────────────────────────────────────────────────────────────────
@bp.route('/perbaikan/add', methods=['GET', 'POST'])
@permission_required('manage_perbaikan')
def tambah_perbaikan():
    semua_aset = Asset.query.order_by(Asset.nama_aset).all()
    # Bisa pre-select aset dari query param (dari halaman detail aset)
    preselect_asset_id = request.args.get('asset_id', type=int)

    if request.method == 'POST':
        asset_id      = request.form.get('asset_id', type=int)
        tgl_str       = request.form.get('tanggal_perbaikan')
        deskripsi     = request.form.get('deskripsi', '').strip()
        biaya         = float(request.form.get('biaya_perbaikan', 0) or 0)

        if not asset_id or not tgl_str or not deskripsi:
            flash('Aset, tanggal, dan deskripsi perbaikan wajib diisi.', 'danger')
            return redirect(url_for('main.tambah_perbaikan'))

        try:
            tgl = datetime.strptime(tgl_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Format tanggal tidak valid.', 'danger')
            return redirect(url_for('main.tambah_perbaikan'))

        asset = Asset.query.get_or_404(asset_id)

        new_p = PerbaikanAset(
            asset_id          = asset_id,
            tanggal_perbaikan = tgl,
            deskripsi         = deskripsi,
            biaya_perbaikan   = biaya
        )
        if not new_p.validasi_status():
            flash('Data perbaikan tidak valid atau belum lengkap.', 'danger')
            return redirect(url_for('main.tambah_perbaikan'))

        new_p.insert_data()

        # Akumulasi otomatis biaya_perawatan pada aset
        _recalculate_biaya(asset)

        flash(f'Data perbaikan berhasil ditambahkan. Biaya perawatan aset "{asset.nama_aset}" '
              f'diperbarui menjadi Rp {asset.biaya_perawatan:,.0f}.', 'success')
        return redirect(url_for('main.perbaikan'))

    return render_template('add_perbaikan.html',
                           semua_aset=semua_aset,
                           preselect_asset_id=preselect_asset_id,
                           today=date.today().isoformat())


# ── EDIT ──────────────────────────────────────────────────────────────────────
@bp.route('/perbaikan/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('manage_perbaikan')
def edit_perbaikan(id):
    p = PerbaikanAset.query.get_or_404(id)
    semua_aset = Asset.query.order_by(Asset.nama_aset).all()

    if request.method == 'POST':
        asset_id  = request.form.get('asset_id', type=int)
        tgl_str   = request.form.get('tanggal_perbaikan')
        deskripsi = request.form.get('deskripsi', '').strip()
        biaya     = float(request.form.get('biaya_perbaikan', 0) or 0)

        if not asset_id or not tgl_str or not deskripsi:
            flash('Aset, tanggal, dan deskripsi wajib diisi.', 'danger')
            return redirect(url_for('main.edit_perbaikan', id=id))

        old_asset_id = p.asset_id
        p.asset_id          = asset_id
        p.tanggal_perbaikan = datetime.strptime(tgl_str, '%Y-%m-%d').date()
        p.deskripsi         = deskripsi
        p.biaya_perbaikan   = biaya
        db.session.flush()

        # Recalculate aset lama (jika aset berpindah) & aset baru
        if old_asset_id != asset_id:
            _recalculate_biaya(Asset.query.get(old_asset_id))
        _recalculate_biaya(Asset.query.get(asset_id))

        flash('Data perbaikan berhasil diperbarui.', 'success')
        return redirect(url_for('main.perbaikan'))

    return render_template('edit_perbaikan.html', p=p, semua_aset=semua_aset)


# ── DELETE ────────────────────────────────────────────────────────────────────
@bp.route('/perbaikan/delete/<int:id>')
@permission_required('manage_perbaikan')
def hapus_perbaikan(id):
    p = PerbaikanAset.query.get_or_404(id)
    asset = p.asset
    db.session.delete(p)
    db.session.flush()
    _recalculate_biaya(asset)
    flash('Data perbaikan berhasil dihapus.', 'success')
    return redirect(url_for('main.perbaikan'))
