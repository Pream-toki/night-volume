@echo off
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
start "" pythonw "%~dp0night_volume.py"
exit
