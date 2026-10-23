from flask import render_template, request, redirect, url_for, flash
from app.models import db, AsistenLab
from app.routes import bp
from app.utils import admin_required

# --- LIST ---
@bp.route('/asisten-lab')
@admin_required
def asisten_lab():
    all_asisten = AsistenLab.query.all()
    return render_template('asisten_lab.html', asisten_list=all_asisten)

# --- ADD ---
@bp.route('/asisten-lab/add', methods=['GET', 'POST'])
@admin_required
def tambah_asisten_lab():
    if request.method == 'POST':
        kode_asisten = request.form['kode_asisten']
        nama = request.form['nama']
        
        # Check uniqueness of Kode Asisten
        if AsistenLab.query.filter_by(kode_asisten=kode_asisten).first():
            flash('Kode Asisten sudah ada!', 'danger')
            return redirect(url_for('main.tambah_asisten_lab'))
            
        new_asisten = AsistenLab(
            kode_asisten=kode_asisten,
            nama=nama
        )
        db.session.add(new_asisten)
        db.session.commit()
        flash('Data Asisten Lab berhasil ditambahkan')
        return redirect(url_for('main.asisten_lab'))
    
    return render_template('add_asisten_lab.html')

# --- EDIT ---
@bp.route('/asisten-lab/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_asisten_lab(id):
    a = AsistenLab.query.get_or_404(id)
    if request.method == 'POST':
        a.kode_asisten = request.form['kode_asisten']
        a.nama = request.form['nama']
        
        db.session.commit()
        flash('Data Asisten Lab berhasil diperbarui')
        return redirect(url_for('main.asisten_lab'))
    return render_template('edit_asisten_lab.html', asisten=a)

# --- DELETE ---
@bp.route('/asisten-lab/delete/<int:id>')
@admin_required
def delete_asisten_lab(id):
    a = AsistenLab.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    flash('Data Asisten Lab berhasil dihapus')
    return redirect(url_for('main.asisten_lab'))
