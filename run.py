import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app import create_apps
import os
import threading
import time
import subprocess
import webbrowser
import socket

app = create_apps()

def find_free_port(default_port=5000):
    """Mencoba port default terlebih dahulu, jika terpakai cari port lain yang kosong."""
    # Tes apakah default port bebas
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', default_port))
            return default_port
    except OSError:
        print(f"\n⚠️ [Info] Port {default_port} sedang digunakan aplikasi lain.")
        print("🔍 Mencari port alternatif yang tersedia...\n")
        # Coba port alternatif dari 5001 hingga 5050
        for port in range(default_port + 1, default_port + 51):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    print(f"✅ [Sukses] Port gratis ditemukan: {port}\n")
                    return port
            except OSError:
                continue
        # Jika 5000-5050 penuh, biarkan sistem operasi memberikan port bebas secara acak
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            _, free_port = s.getsockname()
            print(f"✅ [Sukses] Port gratis sistem diassign: {free_port}\n")
            return free_port

def open_edge(target_port):
    # Menunggu 1.5 detik agar server Flask sudah berjalan sepenuhnya di port target
    time.sleep(1.5)
    url = f"http://127.0.0.1:{target_port}"
    try:
        # Menjalankan Microsoft Edge secara spesifik di OS Windows
        subprocess.Popen(['cmd', '/c', f'start msedge {url}'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Fallback ke browser default sistem jika ada error atau Edge tidak tesedia
        webbrowser.open(url)

if __name__ == '__main__':
    # Set debug secara eksplisit
    app.debug = True

    # Jika berjalan sebagai proses worker (WERKZEUG_RUN_MAIN == 'true'), gunakan port yang sudah ditentukan
    # oleh proses utama agar reloader tidak berpindah port sendiri.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' and 'FLASK_RUN_PORT' in os.environ:
        port = int(os.environ['FLASK_RUN_PORT'])
    else:
        port = find_free_port(5000)
        os.environ['FLASK_RUN_PORT'] = str(port)

    # Jalankan pembuka browser hanya di proses worker reloader (atau di proses utama jika debug=False)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        threading.Thread(target=open_edge, args=(port,), daemon=True).start()

    print(f"🚀 Mempersembahkan Server Aplikasi pada: http://127.0.0.1:{port}/")
    app.run(host='0.0.0.0', port=port)

