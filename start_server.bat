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
    echo Make sure to:
    echo 1. Add PostgreSQL bin directory to PATH
    echo 2. Set up a password for postgres user
    echo 3. Note down the port number ^(default: 5432^)
    echo After installation, run this script again.
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env
    echo Created .env file. Please update it with your configuration.
    echo Press any key to continue after updating .env file...
    pause >nul
)

:: Create required directories
if not exist "logs" mkdir logs
if not exist "instance" mkdir instance

:: Initialize database
echo Initializing database...
python init_db.py
if errorlevel 1 (
    echo Database initialization failed! Please check the logs.
    pause
    exit /b 1
)

:: Start the server manager
echo Starting server manager...
python server_manager.py

:: Keep the window open if there's an error
pause
