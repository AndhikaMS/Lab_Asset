from flask import render_template, request, redirect, url_for, flash
from app.models import db, KepalaLab
from app.routes import bp
from app.utils import permission_required

# --- LIST ---
@bp.route('/kepala-lab')
@permission_required('view_master')
def kepala_lab():
    all_kepala = KepalaLab.query.all()
    return render_template('kepala_lab.html', kepala_list=all_kepala)

# --- ADD ---
@bp.route('/kepala-lab/add', methods=['GET', 'POST'])
@permission_required('edit_master')
def tambah_kepala_lab():
    if request.method == 'POST':
        nik = request.form['nik']
        nama = request.form['nama']
        periode = request.form['periode']
        
        # Check uniqueness of NIK
        if KepalaLab.query.filter_by(nik=nik).first():
            flash('NIK sudah ada!', 'danger')
            return redirect(url_for('main.tambah_kepala_lab'))
            
        is_active = 'is_active' in request.form

        if is_active:
            # Set all others to inactive
            KepalaLab.query.update({KepalaLab.is_active: False})
            
        new_kepala = KepalaLab(
            nik=nik,
            nama=nama, 
            periode=periode,
            is_active=is_active
        )
        new_kepala.insert_data()
        flash('Data Kepala Lab berhasil ditambahkan')
        return redirect(url_for('main.kepala_lab'))
    
    return render_template('add_kepala_lab.html')

# --- EDIT ---
@bp.route('/kepala-lab/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('edit_master')
def edit_kepala_lab(id):
    k = KepalaLab.query.get_or_404(id)
    if request.method == 'POST':
        is_active = 'is_active' in request.form
        if is_active:
            # Set all others to inactive
            KepalaLab.query.update({KepalaLab.is_active: False})
        
        k.update_data(
            nik=request.form['nik'],
            nama=request.form['nama'],
            periode=request.form['periode'],
            is_active=is_active
        )
        flash('Data Kepala Lab berhasil diperbarui')
        return redirect(url_for('main.kepala_lab'))
    return render_template('edit_kepala_lab.html', kepala=k)

# --- DELETE ---
@bp.route('/kepala-lab/delete/<int:id>')
@permission_required('edit_master')
def delete_kepala_lab(id):
    k = KepalaLab.query.get_or_404(id)
    k.delete_data()
    flash('Data Kepala Lab berhasil dihapus')
    return redirect(url_for('main.kepala_lab'))
