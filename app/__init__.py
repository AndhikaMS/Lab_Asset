from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Import routes and models to register them with the app/DB
    from app import routes, models
    
    # Register blueprints
    app.register_blueprint(routes.bp)

    # Synchronize session permissions dynamically on each request
    @app.before_request
    def sync_user_session():
        from flask import session
        user_id = session.get('user_id')
        if user_id:
            from app.models import User
            user = User.query.get(user_id)
            if not user:
                session.clear()
            else:
                session['username'] = user.username
                session['role'] = user.role
                session['nama_lengkap'] = user.nama_lengkap or user.username
                session['jabatan'] = user.jabatan or user.role
                session['permissions'] = user.get_permissions_list()

    # Register helper functions for Jinja2 templates
    def has_permission(perm):
        from flask import session
        perms = session.get('permissions', [])
        role = session.get('role', '')
        if role in ['admin', 'Super Admin'] or 'all' in perms or perm in perms:
            return True
        return False

    app.jinja_env.globals.update(enumerate=enumerate, has_permission=has_permission)

    # Initialize schema additions if needed
    from app.utils import init_db_schema
    init_db_schema(app)

    # Custom error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app
