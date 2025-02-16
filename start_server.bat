@echo off
echo Starting Terminusa Online Server...

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.10 or later.
    pause
    exit /b 1
)

:: Check if virtual environment exists, create if it doesn't
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment and install dependencies
call venv\Scripts\activate
echo Installing/Updating dependencies...
pip install -r requirements-base.txt

:: Start the server
echo Starting server...
python run_server.py

:: Keep the window open if there's an error
pause
