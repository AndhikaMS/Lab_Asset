from datetime import datetime
from app import db
import json

ALL_PERMISSIONS = {
    'view_dashboard': 'Melihat Dasbor Utama & Grafik Metrik KPI',
    'view_master': 'Melihat Data Master (Lokasi, Kategori, Prodi, Kepala Lab)',
    'edit_master': 'Menambah, Mengedit, & Menghapus Data Master',
    'view_assets': 'Melihat Daftar Aset & Detail Informasi Barang',
    'edit_assets': 'Menambah, Mengedit, & Menghapus Data Aset Lab',
    'print_reports': 'Mencetak Laporan Aset, Label QR, & Laporan Data Master',
    'view_spk': 'Melihat Analisis Prioritas Penggantian & Kelayakan Aset',
    'edit_spk_bobot': 'Mengatur Bobot Kriteria Prioritas Penggantian',
    'view_perbaikan': 'Melihat Histori & Tracking Status Perbaikan',
    'manage_perbaikan': 'Mengajukan Perbaikan / Persetujuan ACC Pimpinan',
    'view_floor_plan': 'Melihat & Memetakan Denah 2D Interaktif Laboratorium',
    'manage_users': 'Mengelola Pengguna & Hak Akses Dinamis'
}

class BaseModelMixin:
    """Mixin kelas dasar untuk menyediakan operasi CRUD (Active Record Pattern)
    yang selaras secara 1:1 dengan Class Diagram UML pada laporan sistem."""

    def insert_data(self):
        """Menyimpan entitas baru ke dalam basis data."""
        db.session.add(self)
        db.session.commit()
        return self

    def update_data(self, **kwargs):
        """Memperbarui atribut entitas dan menyimpan perubahan ke basis data."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def delete_data(self):
        """Menghapus entitas dari basis data."""
        db.session.delete(self)
        db.session.commit()
        return True


class User(db.Model, BaseModelMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='admin')
    nama_lengkap = db.Column(db.String(100), nullable=True)
    jabatan = db.Column(db.String(100), nullable=True)
    permissions = db.Column(db.Text, nullable=True)

    def hash_password(self, password):
        """Membuat hash kata sandi terenkripsi (Class Diagram Method)."""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        return self.password_hash

    def verify_password(self, password):
        """Memverifikasi kecocokan kata sandi (Class Diagram Method)."""
        return self.login(password)

    def check_permission(self, perm):
        """Memeriksa hak akses izin dinamis pengguna (Class Diagram Method)."""
        return self.has_permission(perm)

    def login(self, password):
        """Memverifikasi kecocokan kata sandi untuk autentikasi masuk sistem (Class Diagram Method)."""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def logout():
        """Menghapus sesi pengguna aktif dari sistem (Class Diagram Method)."""
        from flask import session, has_request_context
        if has_request_context():
            session.clear()
        return True

    def get_permissions_list(self):
        if self.role in ['admin', 'Super Admin']:
            return list(ALL_PERMISSIONS.keys())
        if not self.permissions:
            return []
        try:
            perms = json.loads(self.permissions)
            return perms if isinstance(perms, list) else []
        except Exception:
            return [p.strip() for p in self.permissions.split(',') if p.strip()]

    def has_permission(self, perm):
        if self.role in ['admin', 'Super Admin'] or 'all' in self.get_permissions_list():
            return True
        return perm in self.get_permissions_list()

    def __repr__(self):
        return f'<User {self.username}>'


class KepalaLab(db.Model, BaseModelMixin):
    __tablename__ = 'kepala_lab'
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    periode = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=False)

    def set_active_period(self, periode_baru, is_active=True):
        """Mengatur status aktif dan periode jabatan kepala laboratorium (Class Diagram Method)."""
        self.periode = periode_baru
        self.is_active = is_active
        db.session.commit()
        return self

    def __repr__(self):
        return self.nama


class Prodi(db.Model, BaseModelMixin):
    __tablename__ = 'prodi'
    id = db.Column(db.Integer, primary_key=True)
    kode_aset = db.Column(db.String(20), nullable=False)
    kode_prodi = db.Column(db.String(20), unique=True, nullable=False)
    nama_prodi = db.Column(db.String(100), nullable=False)

    def get_prodi_code(self):
        """Mengambil kode singkatan dan segmen kode aset prodi (Class Diagram Method)."""
        return f"{self.kode_prodi} ({self.kode_aset})"

    def __repr__(self):
        return self.nama_prodi


class Location(db.Model, BaseModelMixin):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    nama_lab = db.Column(db.String(50), nullable=False)
    kode_aset = db.Column(db.String(20), nullable=True) # Manually entered code (e.g. 1, 2)
    kode_lab = db.Column(db.String(20), unique=True)
    kapasitas = db.Column(db.Integer)
    denah_image = db.Column(db.String(255), nullable=True) # Gambar background denah lab (opsional)
    layout_config = db.Column(db.Text, nullable=True) # Konfigurasi JSON in-app vector/canvas layout
    
    # Relationship
    assets = db.relationship('Asset', backref='location', lazy=True)

    def update_layout_json(self, layout_config_data):
        """Memperbarui konfigurasi JSON tata letak denah kanvas 2D (Class Diagram Method)."""
        return self.save_layout(layout_config_data)

    def get_capacity_status(self):
        """Mengembalikan status kapasitas dan jumlah aset terpasang (Class Diagram Method)."""
        total_installed = len(self.assets) if self.assets else 0
        return f"{total_installed} / {self.kapasitas or 0} Meja"

    def save_layout(self, layout_config_data):
        """Menyimpan konfigurasi JSON tata letak denah kanvas 2D ke basis data (Class Diagram Method)."""
        if isinstance(layout_config_data, (dict, list)):
            self.layout_config = json.dumps(layout_config_data)
        else:
            self.layout_config = layout_config_data
        db.session.commit()
        return self

    def __repr__(self):
        return self.nama_lab


class Category(db.Model, BaseModelMixin):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    nama_kategori = db.Column(db.String(50), nullable=False, unique=True)
    
    # Relationship
    assets = db.relationship('Asset', backref='category', lazy=True)

    def get_total_assets(self):
        """Menghitung total aset yang berada di bawah kategori ini (Class Diagram Method)."""
        return len(self.assets) if self.assets else 0

    def __repr__(self):
        return self.nama_kategori


class KodeLokasi(db.Model, BaseModelMixin):
    __tablename__ = 'kode_lokasi'
    id = db.Column(db.Integer, primary_key=True)
    yayasan = db.Column(db.String(4))
    rektorat = db.Column(db.String(2))
    fakultas = db.Column(db.String(2))
    prodi_id = db.Column(db.Integer, db.ForeignKey('prodi.id'))
    ruangan = db.Column(db.String(2))
    
    # Relationship
    prodi = db.relationship('Prodi', backref='kode_lokasi_refs', lazy=True)

    def build_12_digit_code(self):
        """Menyusun segmen hierarki kode lokasi institusi 12 digit (Class Diagram Method)."""
        p_code = self.prodi.kode_aset if self.prodi else "00"
        return f"{self.yayasan or ''}.{self.rektorat or ''}.{self.fakultas or ''}.{p_code}.{self.ruangan or ''}"


class KodeBarang(db.Model, BaseModelMixin):
    __tablename__ = 'kode_barang'
    id = db.Column(db.Integer, primary_key=True)
    golongan = db.Column(db.String(2))
    bidang = db.Column(db.String(2))
    kelompok = db.Column(db.String(2))
    subkelompok = db.Column(db.String(2))
    tahun_pengadaan = db.Column(db.String(4))
    urutan_ruangan_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    nomor_urut = db.Column(db.String(2))
    
    # Relationship
    location = db.relationship('Location', backref='kode_barang_refs', lazy=True)

    def build_15_digit_code(self):
        """Menyusun segmen klasifikasi kode barang 15 digit (Class Diagram Method)."""
        u_code = self.location.kode_aset if self.location else "0"
        return f"{self.golongan or ''}.{self.bidang or ''}.{self.kelompok or ''}.{self.subkelompok or ''} / {self.tahun_pengadaan or ''} / {u_code}{self.nomor_urut or ''}"


class Asset(db.Model, BaseModelMixin):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    kode_aset = db.Column(db.String(50), unique=True, nullable=False)
    nama_aset = db.Column(db.String(100), nullable=False)
    kategori_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    lokasi_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    prodi_id = db.Column(db.Integer, db.ForeignKey('prodi.id'), nullable=True) 
    
    # New separate code tables
    kode_lokasi_id = db.Column(db.Integer, db.ForeignKey('kode_lokasi.id'), nullable=True)
    kode_barang_id = db.Column(db.Integer, db.ForeignKey('kode_barang.id'), nullable=True)
    
    deskripsi = db.Column(db.Text)
    kondisi = db.Column(db.String(20)) 
    tahun_pengadaan = db.Column(db.Integer)
    qr_code_path = db.Column(db.String(255))
    foto_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Posisi Spasial Denah 2D (dalam persentase 0 - 100%) ---
    pos_x = db.Column(db.Float, nullable=True)
    pos_y = db.Column(db.Float, nullable=True)

    # --- Data Ekonomis (untuk Straight Line & SPK) ---
    harga_perolehan = db.Column(db.Float, nullable=True, default=0)
    umur_ekonomis = db.Column(db.Integer, nullable=True, default=0)  # dalam tahun
    nilai_residu = db.Column(db.Float, nullable=True, default=0)
    skor_kerusakan = db.Column(db.Integer, nullable=True, default=1)  # Skala 1-5 (C2: benefit)
    biaya_perawatan = db.Column(db.Float, nullable=True, default=0)   # Akumulasi biaya servis (C3: benefit)

    # Relationships
    prodi = db.relationship('Prodi', backref='assets', lazy=True)
    kode_lokasi = db.relationship('KodeLokasi', backref='asset', lazy=True)
    kode_barang = db.relationship('KodeBarang', backref='asset', lazy=True)
    perbaikan_list = db.relationship('PerbaikanAset', backref='asset', lazy=True,
                                     cascade='all, delete-orphan',
                                     order_by='PerbaikanAset.tanggal_perbaikan.desc()')

    def sisa_umur_ekonomis(self):
        """Menghitung sisa umur ekonomis berdasarkan tahun perolehan & tahun berjalan."""
        if not self.tahun_pengadaan or not self.umur_ekonomis:
            return 0
        tahun_sekarang = datetime.utcnow().year
        sisa = self.umur_ekonomis - (tahun_sekarang - self.tahun_pengadaan)
        return max(sisa, 0)

    def nilai_buku(self):
        """Menghitung nilai buku aset saat ini menggunakan metode Straight Line."""
        if not self.harga_perolehan or not self.umur_ekonomis or self.umur_ekonomis == 0:
            return self.harga_perolehan or 0
        penyusutan_per_tahun = (self.harga_perolehan - (self.nilai_residu or 0)) / self.umur_ekonomis
        tahun_terpakai = datetime.utcnow().year - (self.tahun_pengadaan or datetime.utcnow().year)
        total_penyusutan = penyusutan_per_tahun * tahun_terpakai
        nb = self.harga_perolehan - total_penyusutan
        return max(nb, self.nilai_residu or 0)

    def penyusutan_per_tahun(self):
        """Menghitung nilai penyusutan tahunan (Straight Line)."""
        if not self.harga_perolehan or not self.umur_ekonomis or self.umur_ekonomis == 0:
            return 0
        return (self.harga_perolehan - (self.nilai_residu or 0)) / self.umur_ekonomis

    def format_kode_lokasi(self):
        """Format kode lokasi dengan notasi titik (misal: 1043.01.06.00.03)."""
        if self.kode_aset:
            parts = self.kode_aset.split(' ')
            if len(parts) >= 5:
                return ".".join(parts[:5])
        return self.kode_aset or ""

    def format_kode_barang(self):
        """Format kode barang resmi (misal: 03.02.01.00 / 2018 / 201)."""
        if self.kode_aset:
            parts = self.kode_aset.split(' ')
            if len(parts) >= 11:
                return f"{'.'.join(parts[5:9])} / {parts[9]} / {parts[10]}"
            elif len(parts) > 5:
                return " ".join(parts[5:])
        return ""

    def format_label(self):
        """Format label inventaris lengkap (misal: 1043.01.06.00.03 / 03.02.01.00 / 2018 / 201)."""
        kl = self.format_kode_lokasi()
        kb = self.format_kode_barang()
        if kl and kb:
            return f"{kl} / {kb}"
        return self.kode_aset or ""

    def update_posisi_denah(self, pos_x, pos_y):
        """Memperbarui koordinat spasial 2D aset pada denah laboratorium (Class Diagram Method)."""
        self.pos_x = float(pos_x)
        self.pos_y = float(pos_y)
        db.session.commit()
        return self

    def generate_qr_code(self):
        """Menghasilkan citra barcode matriks QR Code inventaris (Class Diagram Method)."""
        from app.utils.qr_generator import generate_qr_code
        return generate_qr_code(self)

    def delete_data(self):
        """Menghapus entitas aset beserta relasi kode pembentuknya dari basis data (Class Diagram Method)."""
        if self.kode_lokasi:
            db.session.delete(self.kode_lokasi)
        if self.kode_barang:
            db.session.delete(self.kode_barang)
        db.session.delete(self)
        db.session.commit()
        return True

    def __repr__(self):
        return f'<Asset {self.nama_aset} ({self.kode_aset})>'


class BobotSAW(db.Model, BaseModelMixin):
    """Menyimpan bobot kriteria SAW per kategori aset.
    kategori_id = NULL berarti bobot default (dipakai jika kategori tidak punya bobot khusus).
    """
    __tablename__ = 'bobot_saw'
    id = db.Column(db.Integer, primary_key=True)
    kategori_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, unique=True)
    bobot_c1 = db.Column(db.Float, default=0.4)   # Sisa umur ekonomis (cost)
    bobot_c2 = db.Column(db.Float, default=0.35)  # Tingkat kerusakan fisik (benefit)
    bobot_c3 = db.Column(db.Float, default=0.25)  # Biaya perawatan historis (benefit)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    kategori = db.relationship('Category', backref='bobot_saw', lazy=True)

    def validate_total_bobot(self):
        """Memvalidasi jumlah total bobot bernilai 1.0 atau 100% (Class Diagram Method)."""
        total = round(float(self.bobot_c1 or 0) + float(self.bobot_c2 or 0) + float(self.bobot_c3 or 0), 2)
        return total == 1.0

    def get_weights_vector(self):
        """Mengembalikan vektor pembobotan preferensi kriteria [W1, W2, W3] (Class Diagram Method)."""
        return [float(self.bobot_c1 or 0), float(self.bobot_c2 or 0), float(self.bobot_c3 or 0)]

    def update_bobot(self, c1, c2, c3):
        """Memperbarui nilai bobot kriteria preferensi SAW (Class Diagram Method)."""
        self.bobot_c1 = float(c1)
        self.bobot_c2 = float(c2)
        self.bobot_c3 = float(c3)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self

    def hitung_prioritas(self, assets=None):
        """Mengeksekusi perhitungan SAW untuk daftar aset terkait (Class Diagram Method)."""
        from app.routes.spk import hitung_saw
        if assets is None:
            if self.kategori_id:
                assets = Asset.query.filter_by(kategori_id=self.kategori_id).all()
            else:
                assets = Asset.query.all()
        return hitung_saw(assets, self)

    def __repr__(self):
        return f'<BobotSAW kat={self.kategori_id} ({self.bobot_c1}, {self.bobot_c2}, {self.bobot_c3})>'


# Alias untuk menyelaraskan nama kelas pada Class Diagram skripsi (Tabel 4.4)
BobotKriteria = BobotSAW


class PerbaikanAset(db.Model, BaseModelMixin):
    """Log histori perbaikan / servis per aset."""
    __tablename__ = 'perbaikan_aset'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    tanggal_perbaikan = db.Column(db.Date, nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    biaya_perbaikan = db.Column(db.Float, nullable=False, default=0)
    teknisi = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def hitung_biaya_perilaku(self):
        """Mengembalikan nominal pengeluaran biaya perbaikan rekaman ini (Class Diagram Method)."""
        return float(self.biaya_perbaikan or 0)

    def update_status_servis(self, status_baru):
        """Memperbarui status pengerjaan servis pemeliharaan (Class Diagram Method)."""
        self.status = status_baru
        db.session.commit()
        return self

    def validasi_status(self):
        """Memvalidasi status kelengkapan data perbaikan sebelum diproses (Class Diagram Method)."""
        return bool(self.asset_id and self.tanggal_perbaikan and self.deskripsi and self.biaya_perbaikan is not None)

    def __repr__(self):
        return f'<Perbaikan asset_id={self.asset_id} tgl={self.tanggal_perbaikan}>'
