import subprocess
import sys

def install_dependencies():
    """Install required Python packages"""
    dependencies = [
        'flask-login',
        'flask-sqlalchemy',
        'flask-migrate',
        'psycopg2-binary',
        'python-dotenv'
    ]
    
    for package in dependencies:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {str(e)}")
            raise

if __name__ == '__main__':
    install_dependencies()
