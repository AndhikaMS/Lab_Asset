@echo off
title Instalasi - Lab Asset Management System
cd /d "%~dp0"
cls

echo ================================================================
echo   INSTALASI APLIKASI MANAJEMEN ASET LABORATORIUM (FTI UNIBBA)
echo ================================================================
echo.

:: Cek apakah Python tersedia
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo         Pastikan Python 3.9+ sudah terinstal dan terdaftar di PATH.
    echo         Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] %PY_VER% ditemukan.
echo.

:: Instal dependensi langsung ke Python global (tanpa venv)
echo [Info] Memasang pustaka dependensi dari requirements.txt...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Instalasi gagal. Periksa koneksi internet atau file requirements.txt.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   INSTALASI SELESAI!
echo   Jalankan aplikasi dengan mengklik dua kali: run.bat
echo ================================================================
echo.
pause
