from flask import render_template, session, redirect, url_for
from app.models import Location
from app.routes import bp
from app.utils import permission_required

@bp.route('/locations', methods=['GET'])
@permission_required('view_master')
def locations():
    all_locations = Location.query.all()
    return render_template('locations.html', locations=all_locations)
