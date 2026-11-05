@echo off
title Lab Asset Management System - FTI UNIBBA
cd /d "%~dp0"
cls

echo ================================================================
echo   MENJALANKAN APLIKASI MANAJEMEN ASET LABORATORIUM (FTI UNIBBA)
echo ================================================================
echo.
echo  [Tips] Jangan tutup jendela ini selama menggunakan aplikasi.
echo  [Tips] Tekan CTRL + C untuk menghentikan server.
echo.

:: Cek Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo         Jalankan install.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

:: Aktifkan virtual environment jika ada
if exist "venv\Scripts\activate.bat" (
    echo [Info] Mengaktifkan virtual environment "venv"...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [Info] Mengaktifkan virtual environment ".venv"...
    call .venv\Scripts\activate.bat
) else (
    echo [Info] Menggunakan Python global sistem.
)

echo.
echo [System] Menyiapkan port dan meluncurkan server Flask...
echo.
python run.py

pause
