#!/usr/bin/env python3
import os
import sys
import platform
import ctypes
import subprocess
from typing import Dict, List, Tuple
import psutil
import socket
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemChecker:
    """System requirements and privileges checker"""
    def __init__(self):
        self.os_type = platform.system().lower()
        self.os_release = platform.release()
        self.os_version = platform.version()
        self.machine = platform.machine()
        self.processor = platform.processor()
        
        # Minimum requirements
        self.min_requirements = {
            'cpu_cores': 2,
            'ram_gb': 4,
            'disk_gb': 10,
            'python_version': (3, 8),
            'required_ports': [80, 443, 5000, 8765],
            'required_packages': [
                'python3-dev',
                'python3-pip',
                'python3-venv',
                'build-essential',
                'libssl-dev',
                'libffi-dev',
                'git'
            ]
        }

    def is_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            if self.os_type == 'windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception as e:
            logger.error(f"Error checking admin privileges: {e}")
            return False

    def check_python_version(self) -> bool:
        """Check Python version"""
        current = sys.version_info[:2]
        required = self.min_requirements['python_version']
        
        logger.info(f"Python version: {'.'.join(map(str, current))}")
        return current >= required

    def check_system_resources(self) -> Dict[str, bool]:
        """Check system resources"""
        results = {}
        
        # Check CPU cores
        cpu_cores = psutil.cpu_count(logical=False)
        results['cpu'] = cpu_cores >= self.min_requirements['cpu_cores']
        logger.info(f"CPU cores: {cpu_cores}")
        
        # Check RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)
        results['ram'] = ram_gb >= self.min_requirements['ram_gb']
        logger.info(f"RAM: {ram_gb:.1f} GB")
        
        # Check disk space
        disk = psutil.disk_usage('/')
        disk_gb = disk.free / (1024**3)
        results['disk'] = disk_gb >= self.min_requirements['disk_gb']
        logger.info(f"Free disk space: {disk_gb:.1f} GB")
        
        return results

    def check_ports(self) -> Dict[int, bool]:
        """Check if required ports are available"""
        results = {}
        for port in self.min_requirements['required_ports']:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('localhost', port))
                results[port] = True
            except socket.error:
                results[port] = False
            finally:
                sock.close()
            
            status = "available" if results[port] else "in use"
            logger.info(f"Port {port}: {status}")
        
        return results

    def check_packages(self) -> Dict[str, bool]:
        """Check required system packages"""
        results = {}
        if self.os_type == 'linux':
            for package in self.min_requirements['required_packages']:
                try:
                    subprocess.check_call(
                        ['dpkg', '-s', package],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    results[package] = True
                except subprocess.CalledProcessError:
                    results[package] = False
                
                status = "installed" if results[package] else "missing"
                logger.info(f"Package {package}: {status}")
        else:
            logger.info("Package check skipped (non-Linux system)")
            results = {pkg: True for pkg in self.min_requirements['required_packages']}
        
        return results

    def check_network(self) -> Dict[str, bool]:
        """Check network connectivity"""
        results = {}
        hosts = [
            ('8.8.8.8', 53),  # Google DNS
            ('1.1.1.1', 53),  # Cloudflare DNS
            ('github.com', 443),
            ('pypi.org', 443)
        ]
        
        for host, port in hosts:
            try:
                socket.create_connection((host, port), timeout=5)
                results[host] = True
            except (socket.timeout, socket.error):
                results[host] = False
            
            status = "reachable" if results[host] else "unreachable"
            logger.info(f"Host {host}: {status}")
        
        return results

    def check_write_permissions(self) -> Dict[str, bool]:
        """Check write permissions in required directories"""
        results = {}
        directories = [
            '.',  # Current directory
            'logs',
            'data',
            'config',
            'temp'
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception:
                    pass
            
            test_file = os.path.join(directory, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                results[directory] = True
            except Exception:
                results[directory] = False
            
            status = "writable" if results[directory] else "not writable"
            logger.info(f"Directory {directory}: {status}")
        
        return results

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all system checks"""
        logger.info("Running system checks...")
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'os_type': self.os_type,
                'os_release': self.os_release,
                'os_version': self.os_version,
                'machine': self.machine,
                'processor': self.processor
            },
            'admin': self.is_admin(),
            'python_version': self.check_python_version(),
            'resources': self.check_system_resources(),
            'ports': self.check_ports(),
            'packages': self.check_packages(),
            'network': self.check_network(),
            'permissions': self.check_write_permissions()
        }
        
        # Save results
        os.makedirs('logs', exist_ok=True)
        with open('logs/system_check.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

    def print_results(self, results: Dict[str, Any]):
        """Print check results in a readable format"""
        print("\nSystem Check Results")
        print("===================")
        
        # System Info
        print("\nSystem Information:")
        print(f"OS: {results['system']['os_type']} {results['system']['os_release']}")
        print(f"Version: {results['system']['os_version']}")
        print(f"Machine: {results['system']['machine']}")
        print(f"Processor: {results['system']['processor']}")
        
        # Admin Status
        print("\nPrivileges:")
        print(f"Admin Access: {'Yes' if results['admin'] else 'No'}")
        
        # Python Version
        print("\nPython Version:")
        print(f"Compatible: {'Yes' if results['python_version'] else 'No'}")
        
        # Resources
        print("\nSystem Resources:")
        for resource, status in results['resources'].items():
            print(f"{resource.upper()}: {'OK' if status else 'Insufficient'}")
        
        # Ports
        print("\nRequired Ports:")
        for port, available in results['ports'].items():
            print(f"Port {port}: {'Available' if available else 'In Use'}")
        
        # Packages
        print("\nRequired Packages:")
        for package, installed in results['packages'].items():
            print(f"{package}: {'Installed' if installed else 'Missing'}")
        
        # Network
        print("\nNetwork Connectivity:")
        for host, reachable in results['network'].items():
            print(f"{host}: {'Reachable' if reachable else 'Unreachable'}")
        
        # Permissions
        print("\nDirectory Permissions:")
        for directory, writable in results['permissions'].items():
            print(f"{directory}: {'Writable' if writable else 'Not Writable'}")
        
        # Overall Status
        all_passed = all([
            results['admin'],
            results['python_version'],
            all(results['resources'].values()),
            all(results['ports'].values()),
            all(results['packages'].values()),
            all(results['network'].values()),
            all(results['permissions'].values())
        ])
        
        print("\nOverall Status:")
        if all_passed:
            print("✅ All checks passed - System is ready")
        else:
            print("❌ Some checks failed - See above for details")

def main():
    """Main entry point"""
    checker = SystemChecker()
    
    try:
        results = checker.run_all_checks()
        checker.print_results(results)
        
        # Exit with status code
        all_passed = all([
            results['admin'],
            results['python_version'],
            all(results['resources'].values()),
            all(results['ports'].values()),
            all(results['packages'].values()),
            all(results['network'].values()),
            all(results['permissions'].values())
        ])
        
        return 0 if all_passed else 1
        
    except Exception as e:
        logger.error(f"Error during system check: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
