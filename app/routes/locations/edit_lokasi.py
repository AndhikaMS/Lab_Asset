from flask import render_template, request, redirect, url_for, flash, current_app
from app.models import db, Location, Asset
from app.routes import bp
from app.utils import permission_required
import os
import qrcode

@bp.route('/locations/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('edit_master')
def edit_location(id):
    loc = Location.query.get_or_404(id)
    if request.method == 'POST':
        old_kode_aset = loc.kode_aset
        
        loc.update_data(
            kode_lab=request.form['kode_lab'],
            nama_lab=request.form['nama_lab'],
            kapasitas=request.form['kapasitas'],
            kode_aset=request.form['kode_aset']
        )
        
        new_kode_aset = loc.kode_aset
        
        # Jika kode_aset (urutan lokasi) berubah, update seluruh 27-digit kode aset & QR Code
        if old_kode_aset != new_kode_aset:
            assets = Asset.query.filter_by(lokasi_id=loc.id).all()
            for asset in assets:
                parts = asset.kode_aset.split(' ')
                if len(parts) > 0:
                    last_part = parts[-1]
                    # Asumsikan 2 digit terakhir adalah nomor urut
                    c_no_urut = last_part[-2:]
                    new_last_part = f"{new_kode_aset}{c_no_urut}"
                    parts[-1] = new_last_part
                    
                    new_asset_code = " ".join(parts)
                    asset.kode_aset = new_asset_code
                    
                    from app.utils import generate_asset_qr
                    generate_asset_qr(asset)
                    
        db.session.commit()
        flash('Location updated successfully. Related assets have been updated if Kode Aset changed.')
        return redirect(url_for('main.locations'))
    return render_template('edit_location.html', loc=loc)
