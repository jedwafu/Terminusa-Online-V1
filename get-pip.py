#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import shutil
from urllib.request import urlopen

def download_get_pip():
    """Download get-pip.py from PyPA"""
    url = "https://bootstrap.pypa.io/get-pip.py"
    print(f"Downloading get-pip.py from {url}...")
    
    try:
        with urlopen(url) as response:
            return response.read()
    except Exception as e:
        print(f"Error downloading get-pip.py: {e}")
        return None

def install_pip():
    """Install or upgrade pip"""
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download get-pip.py
            content = download_get_pip()
            if not content:
                return False
            
            # Save to temporary file
            temp_file = os.path.join(temp_dir, "get-pip.py")
            with open(temp_file, "wb") as f:
                f.write(content)
            
            # Execute get-pip.py
            print("Installing/upgrading pip...")
            subprocess.check_call([sys.executable, temp_file, "--isolated"])
            
            print("Pip installation successful!")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing get-pip.py: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def verify_pip():
    """Verify pip installation"""
    try:
        # Check pip version
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Pip version: {result.stdout.strip()}")
            return True
        else:
            print("Pip not found")
            return False
            
    except Exception as e:
        print(f"Error verifying pip: {e}")
        return False

def setup_pip():
    """Set up pip"""
    # Check if pip is already installed
    if verify_pip():
        try:
            # Upgrade pip
            print("Upgrading pip...")
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip"
            ])
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error upgrading pip: {e}")
            return False
    else:
        # Install pip
        return install_pip()

def main():
    """Main entry point"""
    print("Setting up pip...")
    
    if setup_pip():
        print("\nPip setup completed successfully!")
        print("\nYou can now run:")
        print("1. python -m pip install -r requirements.txt")
        print("2. python install_dependencies.py")
        return 0
    else:
        print("\nPip setup failed!")
        print("Please try running this script with administrator privileges")
        print("or install pip manually from https://pip.pypa.io/")
        return 1

if __name__ == "__main__":
    sys.exit(main())
