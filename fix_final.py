"""
Final fix script to resolve the internal server error
"""
import os
import sys
import subprocess
import time

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    if stdout:
        print(f"Output: {stdout}")
    if stderr:
        print(f"Error: {stderr}")
    
    return process.returncode

def fix_final():
    """Apply all fixes to resolve the internal server error"""
    print("Starting final fix process...")
    
    # Execute the announcement model fix with correct indentation
    print("\n1. Fixing Announcement model with correct indentation...")
    run_command("python fix_announcement_indentation.py")
    
    # Execute the init file fix
    print("\n2. Fixing models/__init__.py...")
    run_command("python fix_init.py")
    
    # Create the announcements table
    print("\n3. Creating announcements table...")
    run_command("python create_announcements_table.py")
    
    # Restart the web application
    print("\n4. Restarting the web application...")
    
    # Check if we're using systemd
    if os.path.exists("/etc/systemd/system/terminusa.service"):
        run_command("sudo systemctl restart terminusa")
    else:
        # Try to find and kill the current process
        run_command("pkill -f 'python.*web_app.py'")
        time.sleep(2)  # Wait for process to terminate
        
        # Start the web application in the background
        run_command("nohup python web_app.py > logs/web_app.log 2>&1 &")
    
    print("\nAll fixes have been applied and the web application has been restarted.")
    print("Please check if the internal server error is resolved.")

if __name__ == "__main__":
    fix_final()
