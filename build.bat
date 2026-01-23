@echo off
echo Installing requirements...
pip install -r requirements.txt

echo Building Executable...
pyinstaller --noconfirm --onedir --windowed --add-data "assets;assets" --collect-all customtkinter --name "CertificateGenerator" gui_app.py

echo Build Complete.
echo You can find the executable in the 'dist\CertificateGenerator' folder.
pause
