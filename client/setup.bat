@echo off
setlocal enabledelayedexpansion

:: Colors for Windows console
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "NC=[0m"

echo %YELLOW%Setting up Terminusa Client...%NC%

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Python is not installed! Please install Python 3.10 or later.%NC%
    pause
    exit /b 1
)

:: Check if virtual environment exists, create if it doesn't
if not exist "venv" (
    echo %YELLOW%Creating virtual environment...%NC%
    python -m venv venv
)

:: Activate virtual environment and install dependencies
call venv\Scripts\activate
echo %YELLOW%Installing dependencies...%NC%
pip install -r requirements.txt

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo %YELLOW%Creating .env file...%NC%
    (
        echo # Server Configuration
        echo API_URL=http://46.250.228.210:5000
        echo DEBUG=False
        echo.
        echo # Client Configuration
        echo CLIENT_VERSION=1.0.0
    ) > .env
    echo %GREEN%.env file created%NC%
)

echo.
echo %GREEN%Setup complete!%NC%
echo.
echo %YELLOW%To start the client:%NC%
echo 1. Activate the virtual environment: %GREEN%venv\Scripts\activate%NC%
echo 2. Run the client: %GREEN%python client.py%NC%
echo.

:: Keep the window open
pause

endlocal
