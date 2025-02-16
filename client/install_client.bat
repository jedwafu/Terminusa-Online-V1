@echo off
echo Creating virtual environment...
python -m venv venv-client

echo Activating virtual environment...
call venv-client\Scripts\activate.bat

echo Installing client dependencies...
pip install -r requirements-client.txt

echo Installation complete!
echo To run the client:
echo 1. Activate the virtual environment: venv-client\Scripts\activate.bat
echo 2. Run the client: python client.py

pause
