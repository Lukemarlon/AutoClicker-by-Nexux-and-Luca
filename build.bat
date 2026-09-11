@echo off
echo ============================================
echo   Auto Clicker wird zu einer .exe gebaut...
echo ============================================
echo.

python -m pip install --upgrade pynput pyinstaller pillow --quiet

echo.
echo Baue exe mit Icon und Versionsinfo...
python -m PyInstaller --onefile --noconsole --name AutoClicker ^
  --icon=icon.ico --version-file=version_info.txt ^
  --clean AutoClicker.py

echo.
if exist dist\AutoClicker.exe (
    echo FERTIG: dist\AutoClicker.exe
) else (
    echo Es ist ein Fehler aufgetreten, bitte die Meldungen oben pruefen.
)
pause
