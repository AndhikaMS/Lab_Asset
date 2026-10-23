from flask import render_template, request, redirect, url_for, flash
from app.models import db, Category
from app.routes import bp
from app.utils import permission_required

@bp.route('/categories/add', methods=['GET', 'POST'])
@permission_required('edit_master')
def tambah_kategori():
    if request.method == 'POST':
        nama_kategori = request.form['nama_kategori']
        
        # Check duplicate
        if Category.query.filter_by(nama_kategori=nama_kategori).first():
            flash('Category already exists')
        else:
            new_cat = Category(nama_kategori=nama_kategori)
            new_cat.insert_data()
            flash('Category added successfully')
            return redirect(url_for('main.categories'))
            
    return render_template('add_category.html')
