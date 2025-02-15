import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
import docker
import requests
from time import sleep

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDeployment(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Copy project files to temp directory
        self._copy_project_files()
        
        # Initialize Docker client
        self.docker_client = docker.from_env()

    def tearDown(self):
        """Clean up after each test"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Clean up Docker containers
        containers = self.docker_client.containers.list(
            filters={'name': 'terminusa-test-'}
        )
        for container in containers:
            container.stop()
            container.remove()

    def _copy_project_files(self):
        """Copy project files to temporary directory"""
        ignore_patterns = [
            '.git',
            '__pycache__',
            '*.pyc',
            'venv',
            'node_modules'
        ]
        
        def ignore_func(dir, files):
            return [f for f in files if any(p in f for p in ignore_patterns)]
        
        shutil.copytree(
            self.project_root,
            os.path.join(self.temp_dir, 'terminusa'),
            ignore=ignore_func,
            dirs_exist_ok=True
        )

    def test_docker_build(self):
        """Test Docker image building"""
        dockerfile_content = """
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
EXPOSE 5001

CMD ["python", "main.py"]
"""
        
        # Create Dockerfile
        with open(os.path.join(self.temp_dir, 'terminusa', 'Dockerfile'), 'w') as f:
            f.write(dockerfile_content)
        
        # Build Docker image
        image, logs = self.docker_client.images.build(
            path=os.path.join(self.temp_dir, 'terminusa'),
            tag='terminusa-test:latest',
            rm=True
        )
        
        # Verify image
        self.assertIsNotNone(image)
        self.assertEqual(image.tags[0], 'terminusa-test:latest')

    def test_container_startup(self):
        """Test container startup and health check"""
        # Start container
        container = self.docker_client.containers.run(
            'terminusa-test:latest',
            name='terminusa-test-app',
            ports={
                '5000/tcp': 5000,
                '5001/tcp': 5001
            },
            detach=True
        )
        
        try:
            # Wait for startup
            max_retries = 30
            retry_delay = 1
            
            for _ in range(max_retries):
                try:
                    response = requests.get('http://localhost:5000/health')
                    if response.status_code == 200:
                        break
                except requests.exceptions.ConnectionError:
                    sleep(retry_delay)
            else:
                self.fail("Container failed to start properly")
            
            # Verify container logs
            logs = container.logs().decode('utf-8')
            self.assertIn("Server started", logs)
            
        finally:
            container.stop()
            container.remove()

    def test_database_migration(self):
        """Test database migration process"""
        # Create migration script
        migration_script = """
from flask import Flask
from flask_migrate import Migrate, upgrade
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
migrate = Migrate(app, db)

def run_migrations():
    with app.app_context():
        upgrade()

if __name__ == '__main__':
    run_migrations()
"""
        
        migrations_dir = os.path.join(self.temp_dir, 'terminusa', 'migrations')
        os.makedirs(migrations_dir, exist_ok=True)
        
        with open(os.path.join(migrations_dir, 'migrate.py'), 'w') as f:
            f.write(migration_script)
        
        # Run migration
        result = subprocess.run(
            [sys.executable, 'migrations/migrate.py'],
            cwd=os.path.join(self.temp_dir, 'terminusa'),
            capture_output=True
        )
        
        self.assertEqual(result.returncode, 0)

    def test_static_file_serving(self):
        """Test static file serving in production"""
        # Create test static files
        static_dir = os.path.join(self.temp_dir, 'terminusa', 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        with open(os.path.join(static_dir, 'test.css'), 'w') as f:
            f.write('body { background: #fff; }')
        
        # Start container with static files
        container = self.docker_client.containers.run(
            'terminusa-test:latest',
            name='terminusa-test-static',
            ports={'5000/tcp': 5000},
            detach=True
        )
        
        try:
            # Wait for startup
            sleep(5)
            
            # Test static file access
            response = requests.get('http://localhost:5000/static/test.css')
            self.assertEqual(response.status_code, 200)
            self.assertIn('background: #fff', response.text)
            
        finally:
            container.stop()
            container.remove()

    def test_ssl_configuration(self):
        """Test SSL configuration"""
        # Generate self-signed certificate
        ssl_dir = os.path.join(self.temp_dir, 'terminusa', 'ssl')
        os.makedirs(ssl_dir, exist_ok=True)
        
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', os.path.join(ssl_dir, 'key.pem'),
            '-out', os.path.join(ssl_dir, 'cert.pem'),
            '-days', '365', '-nodes',
            '-subj', '/CN=localhost'
        ])
        
        # Update environment configuration
        env_file = os.path.join(self.temp_dir, 'terminusa', '.env')
        with open(env_file, 'a') as f:
            f.write(f"""
SSL_CERT_PATH={os.path.join(ssl_dir, 'cert.pem')}
SSL_KEY_PATH={os.path.join(ssl_dir, 'key.pem')}
""")
        
        # Start container with SSL
        container = self.docker_client.containers.run(
            'terminusa-test:latest',
            name='terminusa-test-ssl',
            ports={'5000/tcp': 5000},
            volumes={
                ssl_dir: {'bind': '/app/ssl', 'mode': 'ro'}
            },
            detach=True
        )
        
        try:
            # Wait for startup
            sleep(5)
            
            # Test HTTPS access
            response = requests.get(
                'https://localhost:5000',
                verify=False  # Self-signed certificate
            )
            self.assertEqual(response.status_code, 200)
            
        finally:
            container.stop()
            container.remove()

    def test_load_balancing(self):
        """Test load balancer configuration"""
        # Create nginx configuration
        nginx_conf = """
events {
    worker_connections 1024;
}

http {
    upstream terminusa {
        server 127.0.0.1:5000;
        server 127.0.0.1:5001;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://terminusa;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
"""
        
        nginx_dir = os.path.join(self.temp_dir, 'terminusa', 'nginx')
        os.makedirs(nginx_dir, exist_ok=True)
        
        with open(os.path.join(nginx_dir, 'nginx.conf'), 'w') as f:
            f.write(nginx_conf)
        
        # Start nginx container
        nginx = self.docker_client.containers.run(
            'nginx:latest',
            name='terminusa-test-nginx',
            ports={'80/tcp': 80},
            volumes={
                os.path.join(nginx_dir, 'nginx.conf'): {
                    'bind': '/etc/nginx/nginx.conf',
                    'mode': 'ro'
                }
            },
            detach=True
        )
        
        try:
            # Wait for startup
            sleep(5)
            
            # Test load balancing
            responses = []
            for _ in range(10):
                response = requests.get('http://localhost')
                responses.append(response.headers.get('X-Served-By'))
            
            # Verify requests were distributed
            unique_servers = set(responses)
            self.assertGreater(len(unique_servers), 1)
            
        finally:
            nginx.stop()
            nginx.remove()

    def test_backup_restore(self):
        """Test backup and restore procedures"""
        # Create backup script
        backup_script = """
import sqlite3
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy('test.db', f'backup_{timestamp}.db')

if __name__ == '__main__':
    backup_database()
"""
        
        backup_dir = os.path.join(self.temp_dir, 'terminusa', 'backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        with open(os.path.join(backup_dir, 'backup.py'), 'w') as f:
            f.write(backup_script)
        
        # Run backup
        result = subprocess.run(
            [sys.executable, 'backup/backup.py'],
            cwd=os.path.join(self.temp_dir, 'terminusa'),
            capture_output=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Verify backup file was created
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_')]
        self.assertGreater(len(backup_files), 0)

if __name__ == '__main__':
    unittest.main()
