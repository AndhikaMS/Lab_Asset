from flask import render_template
from app.models import Category
from app.routes import bp
from app.utils import permission_required

@bp.route('/categories', methods=['GET'])
@permission_required('view_master')
def categories():
    all_categories = Category.query.all()
    return render_template('categories.html', categories=all_categories)
