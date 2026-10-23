from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models import User
from app.routes import bp

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, langsung ke dashboard
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.login(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['nama_lengkap'] = user.nama_lengkap or user.username
            session['jabatan'] = user.jabatan or user.role
            session['permissions'] = user.get_permissions_list()
            return redirect(url_for('main.dashboard'))
        
        flash('Username atau password salah.')
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    User.logout()
    flash('Anda telah berhasil keluar dari sistem.')
    return redirect(url_for('main.login'))
