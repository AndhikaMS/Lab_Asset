from flask import redirect, url_for, flash
from app.models import db, Location
from app.routes import bp
from app.utils import permission_required

@bp.route('/locations/delete/<int:id>')
@permission_required('edit_master')
def delete_location(id):
    loc = Location.query.get_or_404(id)
    # Check if used
    if loc.assets:
        flash('Cannot delete location because it has assets assigned.')
    else:
        loc.delete_data()
        flash('Location deleted successfully')
    return redirect(url_for('main.locations'))
