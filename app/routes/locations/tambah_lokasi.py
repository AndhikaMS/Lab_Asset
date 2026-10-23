from flask import render_template, request, redirect, url_for, flash
from app.models import db, Location
from app.routes import bp
from app.utils import permission_required

@bp.route('/locations/add', methods=['GET', 'POST'])
@permission_required('edit_master')
def tambah_lokasi():
    if request.method == 'POST':
        kode_lab = request.form['kode_lab']
        nama_lab = request.form['nama_lab']
        kapasitas = request.form['kapasitas']
        kode_aset = request.form['kode_aset']
        
        new_loc = Location(kode_lab=kode_lab, nama_lab=nama_lab, kapasitas=kapasitas, kode_aset=kode_aset)
        new_loc.insert_data()
        flash('Location added successfully')
        return redirect(url_for('main.locations'))
    
    return render_template('add_location.html')
