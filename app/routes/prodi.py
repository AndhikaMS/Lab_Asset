from flask import render_template, request, redirect, url_for, flash
from app.models import db, Prodi
from app.routes import bp
from app.utils import permission_required, admin_required

# --- LIST ---
@bp.route('/prodi')
@permission_required('view_master')
def prodi():
    all_prodi = Prodi.query.all()
    return render_template('prodi.html', prodi_list=all_prodi)

# --- ADD ---
@bp.route('/prodi/add', methods=['GET', 'POST'])
@permission_required('edit_master')
def tambah_prodi():
    if request.method == 'POST':
        kode_aset = request.form['kode_aset']
        kode_prodi = request.form['kode_prodi']
        nama_prodi = request.form['nama_prodi']
        
        # Check uniqueness
        if Prodi.query.filter_by(kode_prodi=kode_prodi).first():
            flash('Kode Prodi sudah ada!', 'danger')
            return redirect(url_for('main.tambah_prodi'))
            
        new_prodi = Prodi(
            kode_aset=kode_aset,
            kode_prodi=kode_prodi, 
            nama_prodi=nama_prodi
        )
        new_prodi.insert_data()
        flash('Data Prodi berhasil ditambahkan')
        return redirect(url_for('main.prodi'))
    
    return render_template('add_prodi.html')

# --- EDIT ---
@bp.route('/prodi/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('edit_master')
def edit_prodi(id):
    p = Prodi.query.get_or_404(id)
    if request.method == 'POST':
        p.update_data(
            kode_aset=request.form['kode_aset'],
            kode_prodi=request.form['kode_prodi'],
            nama_prodi=request.form['nama_prodi']
        )
        flash('Data Prodi berhasil diperbarui')
        return redirect(url_for('main.prodi'))
    return render_template('edit_prodi.html', prodi=p)

# --- DELETE ---
@bp.route('/prodi/delete/<int:id>')
@permission_required('edit_master')
def delete_prodi(id):
    p = Prodi.query.get_or_404(id)
    p.delete_data()
    flash('Data Prodi berhasil dihapus')
    return redirect(url_for('main.prodi'))
