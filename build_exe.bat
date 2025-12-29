@echo off
echo ==========================================
echo   Building KindleClippingsToJEX Exe...
echo ==========================================

REM Activate venv
call .venv\Scripts\activate

REM Convert Icon
python utils\convert_icon.py

REM Run PyInstaller
REM --clean: Clean cache
REM --noconsole: Don't show terminal window
REM --onefile: Bundle into single .exe
REM --icon: Set application icon
REM --add-data: Include resources folder (images, styles, json)
REM --name: Output filename

echo Running PyInstaller...
pyinstaller --clean --noconsole --onefile ^
    --name "KindleToJEX" ^
    --icon "resources\icon.ico" ^
    --paths "." ^
    --collect-all "dateparser" ^
    --add-data "resources;resources" ^
    main.py

echo.
echo ==========================================
echo   Build Complete!
echo   Executable is in: dist\KindleToJEX.exe
echo ==========================================
pause
