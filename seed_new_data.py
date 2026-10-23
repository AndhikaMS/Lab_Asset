import os
import sys
import shutil
import json
import qrcode
from datetime import datetime, date

from app import create_app, db
from app.models import (
    Asset, KodeLokasi, KodeBarang, Location, Category, 
    Prodi, PerbaikanAset
)

def run_seed():
    app = create_app()
    with app.app_context():
        print("1. Menghapus seluruh data aset lama dan riwayat terkait...")
        PerbaikanAset.query.delete()
        Asset.query.delete()
        KodeLokasi.query.delete()
        KodeBarang.query.delete()
        db.session.commit()

        # Bersihkan direktori static/qrcodes
        qr_dir = os.path.join(app.root_path, 'static', 'qrcodes')
        if os.path.exists(qr_dir):
            shutil.rmtree(qr_dir)
        os.makedirs(qr_dir, exist_ok=True)

        print("2. Menyiapkan Data Master...")
        # Categories
        cat_komputer = Category.query.filter_by(nama_kategori="Komputer").first()
        if not cat_komputer:
            cat_komputer = Category(nama_kategori="Komputer")
            db.session.add(cat_komputer)

        cat_mebel = Category.query.filter_by(nama_kategori="Mebel").first()
        if not cat_mebel:
            cat_mebel = Category(nama_kategori="Mebel")
            db.session.add(cat_mebel)

        cat_elektronik = Category.query.filter_by(nama_kategori="Elektronik").first()
        if not cat_elektronik:
            cat_elektronik = Category(nama_kategori="Elektronik")
            db.session.add(cat_elektronik)

        # Prodi
        prodi_umum = Prodi.query.filter_by(kode_prodi="00").first()
        if not prodi_umum:
            prodi_umum = Prodi(kode_aset="00", kode_prodi="00", nama_prodi="Umum/Fakultas")
            db.session.add(prodi_umum)

        # Lokasi / Ruangan Lab
        lab1 = Location.query.filter_by(nama_lab="Lab Multimedia").first()
        if not lab1:
            lab1 = Location(nama_lab="Lab Multimedia", kode_aset="1", kode_lab="LAB-MM", kapasitas=40)
            db.session.add(lab1)

        lab2 = Location.query.filter_by(nama_lab="Lab Basis Data").first()
        if not lab2:
            lab2 = Location(nama_lab="Lab Basis Data", kode_aset="2", kode_lab="LAB-BD", kapasitas=40)
            db.session.add(lab2)
        else:
            lab2.kode_aset = "2"
            lab2.denah_image = None
            lab2.layout_config = None

        lab3 = Location.query.filter_by(nama_lab="Laboratorium IOT").first()
        if not lab3:
            lab3 = Location(nama_lab="Laboratorium IOT", kode_aset="3", kode_lab="LAB-03", kapasitas=30)
            db.session.add(lab3)

        db.session.commit()

        print("3. Memasukkan Data Aset ke Lab Basis Data sesuai spesifikasi...")
        
        # Spesifikasi input dari instruksi:
        # Kode Lokasi: 1043.01.06.00.03
        c_yayasan = "1043"
        c_rektorat = "01"
        c_fakultas = "06"
        c_prodi = "00"
        c_lokasi = "03"   # Ruangan Lab Basis Data
        c_tahun = "2018"
        c_urut_lok = "2"  # Lab Basis Data (Lokasi ke-2)

        items_spec = [
            {
                "nama": "PC / Komputer",
                "category": cat_komputer,
                "kode_barang": "03.02.01.00",
                "qty": 21,
                "harga": 6500000,
                "umur": 5,
                "deskripsi_prefix": "Workstation komputer praktikum Lab Basis Data (Core i5, RAM 16GB, SSD 512GB)"
            },
            {
                "nama": "AC (Air Conditioner)",
                "category": cat_elektronik,
                "kode_barang": "03.03.06.00",
                "qty": 2,
                "harga": 3800000,
                "umur": 5,
                "deskripsi_prefix": "Unit pendingin ruangan split wall 2 PK inverter"
            },
            {
                "nama": "Proyektor (LCD)",
                "category": cat_elektronik,
                "kode_barang": "05.02.01.00",
                "qty": 1,
                "harga": 4800000,
                "umur": 5,
                "deskripsi_prefix": "Proyektor LCD resolusi Full HD 3800 ANSI Lumens untuk presentasi dosen"
            }
        ]

        # Koordinat workstation default (4 baris x 5 meja)
        pc_coords = [
            (6.0, 24.0), (21.0, 24.0), (46.0, 24.0), (61.0, 24.0), (76.0, 24.0),
            (6.0, 42.0), (21.0, 42.0), (46.0, 42.0), (61.0, 42.0), (76.0, 42.0),
            (6.0, 60.0), (21.0, 60.0), (46.0, 60.0), (61.0, 60.0), (76.0, 60.0),
            (6.0, 78.0), (21.0, 78.0), (46.0, 78.0), (61.0, 78.0), (76.0, 78.0)
        ]

        created_assets = []
        pc_assets_list = []

        for spec in items_spec:
            kb_parts = spec["kode_barang"].split('.')
            c_gol, c_bid, c_kel, c_sub = kb_parts[0], kb_parts[1], kb_parts[2], kb_parts[3]

            for i in range(1, spec["qty"] + 1):
                c_no_urut = f"{i:02d}"

                # 1. KodeLokasi
                new_kl = KodeLokasi(
                    yayasan=c_yayasan,
                    rektorat=c_rektorat,
                    fakultas=c_fakultas,
                    prodi_id=prodi_umum.id,
                    ruangan=c_lokasi
                )
                db.session.add(new_kl)
                db.session.flush()

                # 2. KodeBarang
                new_kb = KodeBarang(
                    golongan=c_gol,
                    bidang=c_bid,
                    kelompok=c_kel,
                    subkelompok=c_sub,
                    tahun_pengadaan=c_tahun,
                    urutan_ruangan_id=lab2.id,
                    nomor_urut=c_no_urut
                )
                db.session.add(new_kb)
                db.session.flush()

                # Final Code format: 1043 01 06 00 03 03 02 01 00 2018 201
                final_code = f"{c_yayasan} {c_rektorat} {c_fakultas} {c_prodi} {c_lokasi} {c_gol} {c_bid} {c_kel} {c_sub} {c_tahun} {c_urut_lok}{c_no_urut}"

                # Tentukan kondisi dan skor
                if spec["nama"] == "PC / Komputer":
                    # Berikan sedikit variasi untuk demonstrasi visual status warna Floor Plan & SPK
                    if i in [18, 19]:
                        kondisi = 'Rusak Ringan'
                        skor_kerusakan = 2
                        biaya_perawatan = 350000.0
                    elif i == 20:
                        kondisi = 'Rusak Berat'
                        skor_kerusakan = 3
                        biaya_perawatan = 850000.0
                    else:
                        kondisi = 'Baik'
                        skor_kerusakan = 1
                        biaya_perawatan = 0.0
                    
                    pos_x, pos_y = pc_coords[i - 1] if i <= len(pc_coords) else (None, None)
                else:
                    kondisi = 'Baik'
                    skor_kerusakan = 1
                    biaya_perawatan = 0.0
                    pos_x, pos_y = None, None

                # 3. Create Asset
                new_asset = Asset(
                    kode_aset=final_code,
                    nama_aset=f"{spec['nama']} - Unit {i}",
                    kategori_id=spec["category"].id,
                    lokasi_id=lab2.id,
                    prodi_id=prodi_umum.id,
                    kode_lokasi_id=new_kl.id,
                    kode_barang_id=new_kb.id,
                    deskripsi=f"{spec['deskripsi_prefix']} (Unit ke-{i}).",
                    kondisi=kondisi,
                    tahun_pengadaan=int(c_tahun),
                    harga_perolehan=spec["harga"],
                    umur_ekonomis=spec["umur"],
                    nilai_residu=spec["harga"] * 0.10,
                    skor_kerusakan=skor_kerusakan,
                    biaya_perawatan=biaya_perawatan,
                    pos_x=pos_x,
                    pos_y=pos_y
                )
                db.session.add(new_asset)
                db.session.flush()

                # 4. Generate QR Code
                qr_content = f"Kode Aset : {final_code}\nNama Aset : {new_asset.nama_aset}\nLokasi : Lab Basis Data\nDeskripsi : {new_asset.deskripsi}"
                qr = qrcode.make(qr_content)
                qr_filename = f"asset_{new_asset.id}.png"
                qr_path = os.path.join(qr_dir, qr_filename)
                qr.save(qr_path)
                new_asset.qr_code_path = f"qrcodes/{qr_filename}"

                created_assets.append(new_asset)
                if spec["nama"] == "PC / Komputer":
                    pc_assets_list.append(new_asset)

        # Riwayat servis untuk PC Unit 18, 19, 20
        if len(pc_assets_list) >= 20:
            srv1 = PerbaikanAset(
                asset_id=pc_assets_list[17].id,
                tanggal_perbaikan=date(2024, 2, 10),
                deskripsi="Penggantian pasta termal processor dan pembersihan kipas pendingin casing.",
                biaya_perbaikan=150000
            )
            srv2 = PerbaikanAset(
                asset_id=pc_assets_list[18].id,
                tanggal_perbaikan=date(2024, 3, 5),
                deskripsi="Servis port USB depan dan penggantian modul RAM bermasalah.",
                biaya_perbaikan=200000
            )
            srv3 = PerbaikanAset(
                asset_id=pc_assets_list[19].id,
                tanggal_perbaikan=date(2024, 4, 12),
                deskripsi="Power supply drop / mati total dan motherboard short circuit.",
                biaya_perbaikan=850000
            )
            db.session.add_all([srv1, srv2, srv3])

        # 5. Inisialisasi Layout In-App Floor Plan untuk Lab Basis Data
        workstations = []
        rows = [
            (24.0, [('PC-01', 6.0), ('PC-02', 21.0), ('PC-03', 46.0), ('PC-04', 61.0), ('PC-05', 76.0)]),
            (42.0, [('PC-06', 6.0), ('PC-07', 21.0), ('PC-08', 46.0), ('PC-09', 61.0), ('PC-10', 76.0)]),
            (60.0, [('PC-11', 6.0), ('PC-12', 21.0), ('PC-13', 46.0), ('PC-14', 61.0), ('PC-15', 76.0)]),
            (78.0, [('PC-16', 6.0), ('PC-17', 21.0), ('PC-18', 46.0), ('PC-19', 61.0), ('PC-20', 76.0)])
        ]
        idx = 0
        for y, cols in rows:
            for label, x in cols:
                asset_id = pc_assets_list[idx].id if idx < len(pc_assets_list) else None
                workstations.append({
                    'id': f'ws-{idx+1}',
                    'label': label,
                    'x': x,
                    'y': y,
                    'w': 12.5,
                    'h': 12.0,
                    'asset_id': asset_id
                })
                idx += 1

        fixtures = [
            {'id': 'door-1', 'type': 'door', 'label': 'PINTU', 'x': 5.5, 'y': 2.0, 'w': 13.0, 'h': 4.5},
            {'id': 'screen-1', 'type': 'projector', 'label': 'LAYAR PROYEKTOR', 'x': 34.0, 'y': 8.0, 'w': 18.0, 'h': 7.0},
            {'id': 'lecturer-1', 'type': 'lecturer', 'label': 'MEJA DOSEN', 'x': 54.0, 'y': 7.0, 'w': 33.0, 'h': 13.0},
            {'id': 'aisle-1', 'type': 'text', 'label': 'LORONG\nTENGAH', 'x': 35.0, 'y': 48.0, 'w': 8.5, 'h': 8.0},
            {'id': 'ac-1', 'type': 'ac', 'label': 'AC 1', 'x': 10.0, 'y': 94.5, 'w': 15.0, 'h': 4.0},
            {'id': 'ac-2', 'type': 'ac', 'label': 'AC 2', 'x': 67.0, 'y': 94.5, 'w': 15.0, 'h': 4.0}
        ]

        lab2_layout = {
            'room_title': 'LABORATORIUM BASIS DATA (20 PC)',
            'fixtures': fixtures,
            'workstations': workstations
        }
        lab2.layout_config = json.dumps(lab2_layout)

        db.session.commit()
        print(f"SELESAI! Berhasil mendaftarkan {len(created_assets)} aset ke Lab Basis Data.")
        print(f"Total per kategori: PC={len(pc_assets_list)}, Meja=20, Kursi=20, AC=2, Proyektor=1.")

if __name__ == '__main__':
    run_seed()
