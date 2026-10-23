from flask import redirect, url_for, flash, current_app
from app.models import db, Asset
from app.routes import bp
from app.utils import permission_required
import os

@bp.route('/assets/delete/<int:id>')
@permission_required('edit_assets')
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    # Optional: Delete QR image file
    if asset.qr_code_path:
        qr_full_path = os.path.join(current_app.root_path, 'static', asset.qr_code_path)
        if os.path.exists(qr_full_path):
            try:
                os.remove(qr_full_path)
            except:
                pass
                
    asset.delete_data()
    flash('Asset deleted successfully')
    return redirect(url_for('main.assets'))
