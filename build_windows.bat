@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)
%PY% --version
if errorlevel 1 (
  echo.
  echo Python 3.10+ nao encontrado. Instale o Python em python.org
  pause
  exit /b 1
)
echo.
echo Instalando as dependencias...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias.
  pause
  exit /b 1
)
echo.
echo Criando o executavel do HD Launcher...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name "HD Launcher" --icon "assets\hd-launcher.ico" --add-data "assets;assets" hd_launcher.py
if errorlevel 1 (
  echo Falha ao compilar o executavel.
  pause
  exit /b 1
)
echo.
echo PRONTO! Seu launcher esta em: dist\HD Launcher.exe
pause
