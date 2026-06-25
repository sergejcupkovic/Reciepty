@echo off
echo Starting Reciepty...
cd /d "%~dp0"
IF NOT EXIST .venv (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing requirements...
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)
python run.py
pause
