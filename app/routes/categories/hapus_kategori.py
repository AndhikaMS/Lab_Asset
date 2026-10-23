from flask import redirect, url_for, flash
from app.models import db, Category
from app.routes import bp
from app.utils import permission_required

@bp.route('/categories/delete/<int:id>')
@permission_required('edit_master')
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.assets:
        flash('Cannot delete category because it has assets assigned.')
    else:
        cat.delete_data()
        flash('Category deleted successfully')
    return redirect(url_for('main.categories'))
