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

:: Check if PostgreSQL is installed
where psql >nul 2>&1
if errorlevel 1 (
    echo PostgreSQL is not installed!
    echo Please install PostgreSQL from: https://www.postgresql.org/download/windows/
    echo After installation, run this script again.
    pause
    exit /b 1
)

:: Create required directories
if not exist "logs" mkdir logs
if not exist "instance" mkdir instance

:: Start the server manager
echo Starting server manager...
python server_manager.py

:: Keep the window open if there's an error
pause
