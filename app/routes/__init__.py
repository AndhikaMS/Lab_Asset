from flask import Blueprint

bp = Blueprint('main', __name__)

# Import all route modules to register them with the blueprint
from app.routes.auth import auth
from app.routes.main import dashboard
from app.routes.locations import tampil_lokasi, tambah_lokasi, edit_lokasi, hapus_lokasi
from app.routes.categories import tampil_kategori, tambah_kategori, edit_kategori, hapus_kategori
from app.routes.assets import tampil_aset, tambah_aset, edit_aset, hapus_aset, print_aset, detail_aset
from app.routes import prodi, kepala_lab, spk, perbaikan, backup_restore, users, floor_plan
