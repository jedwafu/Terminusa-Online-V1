import os
import shutil

def update_application():
    """
    Update the application with the new files and configurations
    """
    # Update web_app.py
    if os.path.exists('web_app_updated.py'):
        shutil.copy('web_app_updated.py', 'web_app.py')
        print("✓ Updated web_app.py")

    # Ensure static/css directory exists
    os.makedirs('static/css', exist_ok=True)

    # Update announcements template
    if os.path.exists('templates/announcements_updated.html'):
        shutil.copy('templates/announcements_updated.html', 'templates/announcements.html')
        print("✓ Updated announcements.html")

    # Update CSS files
    if os.path.exists('static/css/announcements.css'):
        print("✓ CSS files are in place")

    print("\nUpdate completed successfully!")
    print("\nPlease ensure the following:")
    print("1. The Flask application has been restarted")
    print("2. Any existing database sessions have been closed")
    print("3. The browser cache has been cleared")

if __name__ == "__main__":
    update_application()
