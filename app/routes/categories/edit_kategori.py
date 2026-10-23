from flask import render_template, request, redirect, url_for, flash
from app.models import db, Category
from app.routes import bp
from app.utils import permission_required

@bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('edit_master')
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'POST':
        # Check duplicate if name changed
        new_name = request.form['nama_kategori']
        if new_name != cat.nama_kategori and Category.query.filter_by(nama_kategori=new_name).first():
            flash('Category name already exists')
        else:
            cat.update_data(nama_kategori=new_name)
            flash('Category updated successfully')
            return redirect(url_for('main.categories'))
    return render_template('edit_category.html', cat=cat)
