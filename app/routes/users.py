from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, ALL_PERMISSIONS
from app.routes import bp
from app.utils import permission_required
import json

ROLE_PRESETS = {
    'Super Admin': list(ALL_PERMISSIONS.keys()),
    'Ketua Yayasan': ['view_dashboard', 'view_master', 'view_assets', 'print_reports', 'view_spk', 'view_perbaikan', 'view_floor_plan'],
    'Rektor': ['view_dashboard', 'view_master', 'view_assets', 'print_reports', 'view_spk', 'view_perbaikan', 'view_floor_plan'],
    'Dekan': ['view_dashboard', 'view_master', 'view_assets', 'print_reports', 'view_spk', 'view_perbaikan', 'view_floor_plan'],
    'Kepala Lab': ['view_dashboard', 'view_master', 'edit_master', 'view_assets', 'edit_assets', 'print_reports', 'view_spk', 'edit_spk_bobot', 'view_perbaikan', 'manage_perbaikan', 'view_floor_plan'],
    'Asisten Lab': ['view_dashboard', 'view_assets', 'view_perbaikan', 'manage_perbaikan', 'view_floor_plan']
}

PERMISSION_GROUPS = [
    {
        'id': 'dashboard',
        'title': 'Dasbor & Visualisasi KPI',
        'icon': '📊',
        'description': 'Akses metrik ringkasan portofolio laboratorium dan grafik finansial.',
        'permissions': ['view_dashboard']
    },
    {
        'id': 'master',
        'title': 'Data Master Laboratorium',
        'icon': '🏢',
        'description': 'Master data ruangan lab, klasifikasi kategori, prodi, dan kepala lab.',
        'permissions': ['view_master', 'edit_master']
    },
    {
        'id': 'assets',
        'title': 'Manajemen Aset & Inventaris',
        'icon': '💻',
        'description': 'Inventarisasi fisik, cetak QR code label 27-digit, dan laporan aset.',
        'permissions': ['view_assets', 'edit_assets', 'print_reports']
    },
    {
        'id': 'perbaikan',
        'title': 'Riwayat Servis & Perbaikan',
        'icon': '🔧',
        'description': 'Tracking penanganan kerusakan teknis dan pencatatan histori biaya pemeliharaan.',
        'permissions': ['view_perbaikan', 'manage_perbaikan']
    },
    {
        'id': 'floor_plan',
        'title': 'Pemetaan Denah Laboratorium (2D)',
        'icon': '🗺️',
        'description': 'Akses visual interaktif pemetaan komputer PC-01 s.d. PC-20 pada layout canvas ruangan.',
        'permissions': ['view_floor_plan']
    },
    {
        'id': 'spk',
        'title': 'Prioritas Penggantian (Kelayakan Aset)',
        'icon': '⚖️',
        'description': 'Analisis dan pemeringkatan prioritas peremajaan komputer & penentuan bobot kriteria.',
        'permissions': ['view_spk', 'edit_spk_bobot']
    },
    {
        'id': 'users',
        'title': 'Manajemen Pengguna & Hak Akses',
        'icon': '👥',
        'description': 'Pengelolaan akun pimpinan/asisten, penetapan peran (role), dan konfigurasi izin granular.',
        'permissions': ['manage_users']
    }
]

@bp.route('/users')
@permission_required('manage_users')
def users():
    all_users = User.query.order_by(User.id.asc()).all()
    return render_template('users.html', users=all_users, all_permissions=ALL_PERMISSIONS, permission_groups=PERMISSION_GROUPS)

@bp.route('/users/add', methods=['GET', 'POST'])
@permission_required('manage_users')
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        jabatan = request.form.get('jabatan', '').strip()
        role = request.form.get('role', 'Custom').strip()
        
        # Ambil daftar permisi yang dicentang dari form
        selected_perms = request.form.getlist('permissions')
        if role in ['admin', 'Super Admin'] and not selected_perms:
            selected_perms = list(ALL_PERMISSIONS.keys())

        if not username or not password:
            flash('Username dan password wajib diisi.')
            return redirect(url_for('main.add_user'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f'Username "{username}" sudah terdaftar.')
            return redirect(url_for('main.add_user'))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            nama_lengkap=nama_lengkap,
            jabatan=jabatan,
            permissions=json.dumps(selected_perms)
        )
        new_user.insert_data()

        flash(f'Pengguna "{username}" ({jabatan or role}) berhasil ditambahkan.')
        return redirect(url_for('main.users'))

    return render_template('user_form.html', action='add', all_permissions=ALL_PERMISSIONS, role_presets=ROLE_PRESETS, permission_groups=PERMISSION_GROUPS)

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@permission_required('manage_users')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.nama_lengkap = request.form.get('nama_lengkap', '').strip()
        user.jabatan = request.form.get('jabatan', '').strip()
        user.role = request.form.get('role', user.role).strip()
        
        password = request.form.get('password', '').strip()
        if password:
            user.password_hash = generate_password_hash(password)

        selected_perms = request.form.getlist('permissions')
        if user.role in ['admin', 'Super Admin'] and not selected_perms:
            selected_perms = list(ALL_PERMISSIONS.keys())
        user.permissions = json.dumps(selected_perms)

        db.session.commit()

        # Update session jika mengedit akun sendiri
        if session.get('user_id') == user.id:
            session['username'] = user.username
            session['role'] = user.role
            session['nama_lengkap'] = user.nama_lengkap or user.username
            session['jabatan'] = user.jabatan or user.role
            session['permissions'] = user.get_permissions_list()

        flash(f'Data akun "{user.username}" berhasil diperbarui.')
        return redirect(url_for('main.users'))

    user_perms = user.get_permissions_list()
    return render_template('user_form.html', action='edit', user=user, user_perms=user_perms, all_permissions=ALL_PERMISSIONS, role_presets=ROLE_PRESETS, permission_groups=PERMISSION_GROUPS)

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@permission_required('manage_users')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get('user_id'):
        flash('Anda tidak dapat menghapus akun Anda sendiri.')
        return redirect(url_for('main.users'))

    username = user.username
    user.delete_data()
    flash(f'Pengguna "{username}" telah berhasil dihapus.')
    return redirect(url_for('main.users'))
