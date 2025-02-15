#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import venv
import argparse
import shutil
from typing import List, Optional
from pathlib import Path

class DependencyInstaller:
    """Manages dependency installation"""
    def __init__(self, venv_path: str = '.venv'):
        self.venv_path = venv_path
        self.python_path = self._get_venv_python()
        self.pip_path = self._get_venv_pip()
        self.requirements_file = 'requirements.txt'
        self.dev_requirements_file = 'requirements-dev.txt'
        self.optional_requirements_file = 'requirements-optional.txt'

    def _get_venv_python(self) -> str:
        """Get virtual environment Python path"""
        if platform.system() == 'Windows':
            return os.path.join(self.venv_path, 'Scripts', 'python.exe')
        return os.path.join(self.venv_path, 'bin', 'python')

    def _get_venv_pip(self) -> str:
        """Get virtual environment pip path"""
        if platform.system() == 'Windows':
            return os.path.join(self.venv_path, 'Scripts', 'pip.exe')
        return os.path.join(self.venv_path, 'bin', 'pip')

    def create_virtualenv(self) -> bool:
        """Create virtual environment"""
        try:
            print(f"Creating virtual environment in {self.venv_path}...")
            venv.create(self.venv_path, with_pip=True)
            return True
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            return False

    def install_requirements(
        self,
        dev: bool = False,
        optional: bool = False,
        upgrade: bool = False
    ) -> bool:
        """Install project requirements"""
        try:
            # Install core requirements first
            print("Installing core requirements...")
            cmd = [self.pip_path, 'install']
            if upgrade:
                cmd.append('--upgrade')
            cmd.extend(['-r', self.requirements_file])
            subprocess.run(cmd, check=True)
            
            # Install dev requirements if requested
            if dev and os.path.exists(self.dev_requirements_file):
                print("Installing development requirements...")
                cmd = [self.pip_path, 'install', '-r', self.dev_requirements_file]
                if upgrade:
                    cmd.append('--upgrade')
                subprocess.run(cmd, check=True)
            
            # Install optional requirements if requested
            if optional and os.path.exists(self.optional_requirements_file):
                print("Installing optional requirements...")
                cmd = [self.pip_path, 'install', '-r', self.optional_requirements_file]
                if upgrade:
                    cmd.append('--upgrade')
                subprocess.run(cmd, check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
            return False

    def install_package(
        self,
        package: str,
        version: Optional[str] = None,
        upgrade: bool = False
    ) -> bool:
        """Install a specific package"""
        try:
            cmd = [self.pip_path, 'install']
            
            if upgrade:
                cmd.append('--upgrade')
            
            if version:
                cmd.append(f"{package}=={version}")
            else:
                cmd.append(package)
            
            print(f"Installing {package}...")
            subprocess.run(cmd, check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            return False

    def uninstall_package(self, package: str) -> bool:
        """Uninstall a specific package"""
        try:
            cmd = [self.pip_path, 'uninstall', '-y', package]
            print(f"Uninstalling {package}...")
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error uninstalling {package}: {e}")
            return False

    def update_pip(self) -> bool:
        """Update pip to latest version"""
        try:
            cmd = [self.pip_path, 'install', '--upgrade', 'pip']
            print("Updating pip...")
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error updating pip: {e}")
            return False

    def install_dev_tools(self) -> bool:
        """Install development tools"""
        tools = [
            'black',
            'flake8',
            'mypy',
            'pylint',
            'pytest',
            'pytest-cov',
            'ipython',
            'jupyter'
        ]
        
        success = True
        for tool in tools:
            if not self.install_package(tool):
                success = False
        
        return success

    def setup_git_hooks(self) -> bool:
        """Set up Git pre-commit hooks"""
        try:
            # Install pre-commit
            self.install_package('pre-commit')
            
            # Install hooks
            subprocess.run(
                [self.python_path, '-m', 'pre_commit', 'install'],
                check=True
            )
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error setting up Git hooks: {e}")
            return False

    def clean(self) -> bool:
        """Clean up virtual environment"""
        try:
            if os.path.exists(self.venv_path):
                shutil.rmtree(self.venv_path)
            return True
        except Exception as e:
            print(f"Error cleaning environment: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Install project dependencies'
    )
    
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Install development dependencies'
    )
    
    parser.add_argument(
        '--optional',
        action='store_true',
        help='Install optional dependencies'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean existing virtual environment'
    )
    
    parser.add_argument(
        '--upgrade',
        action='store_true',
        help='Upgrade existing packages'
    )
    
    parser.add_argument(
        '--venv',
        default='.venv',
        help='Virtual environment path'
    )
    
    args = parser.parse_args()
    
    installer = DependencyInstaller(args.venv)
    
    if args.clean:
        print("Cleaning environment...")
        if not installer.clean():
            return 1
    
    # Create virtual environment
    if not os.path.exists(args.venv):
        if not installer.create_virtualenv():
            return 1
    
    # Update pip
    if not installer.update_pip():
        return 1
    
    # Install requirements
    if not installer.install_requirements(
        dev=args.dev,
        optional=args.optional,
        upgrade=args.upgrade
    ):
        return 1
    
    # Install development tools
    if args.dev:
        print("Installing development tools...")
        if not installer.install_dev_tools():
            return 1
        
        print("Setting up Git hooks...")
        if not installer.setup_git_hooks():
            return 1
    
    print("\nInstallation complete!")
    
    # Print next steps
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == 'Windows':
        print(f"   .\\{args.venv}\\Scripts\\activate")
    else:
        print(f"   source {args.venv}/bin/activate")
    
    print("2. Run the tests:")
    print("   python run_tests.py")
    
    print("3. Start the development server:")
    print("   python main.py")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
