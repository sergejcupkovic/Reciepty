@echo off
echo Starting Reciepty...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python run.py
