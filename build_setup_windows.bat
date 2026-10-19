@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo      HD LAUNCHER - CRIADOR DE SETUP v1.7.0
echo ================================================
echo.
echo Este script e para DESENVOLVEDORES.
echo O jogador final NAO precisa instalar Python.
echo.

where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3.12"
) else (
    set "PY=python"
)

%PY% -m venv .venv
if errorlevel 1 goto :pythonError

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :buildError
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :buildError

".venv\Scripts\python.exe" -m unittest discover -s . -p "test_*.py" -v
if errorlevel 1 goto :buildError

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name "HDLauncher" --icon "assets\hd-launcher.ico" --add-data "assets:assets" hd_launcher.py
if errorlevel 1 goto :buildError

if not exist "dist\HDLauncher\HDLauncher.exe" goto :buildError

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo.
    echo Inno Setup 6 nao encontrado.
    echo Instale: https://jrsoftware.org/isinfo.php
    echo Ou use o GitHub Actions sem instalar nada no seu PC.
    pause
    exit /b 1
)

"%ISCC%" setup.iss
if errorlevel 1 goto :buildError

echo.
echo ================================================
echo PRONTO: installer-output\HDLauncher-Setup-v1.7.0.exe
echo ================================================
pause
exit /b 0

:pythonError
echo Falha ao encontrar o Python 3.12 (ou Python no PATH).
echo Para nao instalar Python use a compilacao pelo GitHub Actions.
pause
exit /b 1

:buildError
echo Falha na compilacao. Veja as linhas de erro acima.
pause
exit /b 1
