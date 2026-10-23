from flask import render_template
from app.models import Asset
from app.routes import bp
from app.utils import permission_required

@bp.route('/assets/detail/<int:id>', methods=['GET'])
@permission_required('view_assets')
def detail_asset(id):
    asset = Asset.query.get_or_404(id)
    return render_template('detail_asset.html', asset=asset)
