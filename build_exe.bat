@echo off
echo ==========================================
echo   Building KindleClippingsToJEX Exe...
echo ==========================================

REM Activate venv
call .venv\Scripts\activate

REM Convert Icon if needed (optional check)
python utils\convert_icon.py

echo.
echo Running PyInstaller with Spec File...
echo This will generate both GUI (KindleToJEX.exe) and CLI (KindleToJEX-cli.exe)
echo.

pyinstaller --clean --noconfirm KindleToJEX.spec

echo.
echo ==========================================
echo   Build Complete!
echo   Executables are in: dist\
echo ==========================================
pause
