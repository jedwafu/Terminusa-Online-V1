"""
Fix for circular import issue in models/__init__.py
"""

def fix_init_file():
    """Fix the models/__init__.py file to prevent circular imports"""
    # Read the current content of models/__init__.py
    with open('models/__init__.py', 'r') as f:
        content = f.read()

    # Find and modify the User.announcements relationship
    if "User.announcements = db.relationship('Announcement'" in content:
        # Remove the problematic relationship
        new_content = content.replace(
            "    User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')",
            "    # Relationship moved to avoid circular imports\n    # User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')"
        )
        
        # Write the modified content back to models/__init__.py
        with open('models/__init__.py', 'w') as f:
            f.write(new_content)
        
        print("Successfully modified models/__init__.py")
    else:
        print("The User.announcements relationship was not found in models/__init__.py")

if __name__ == "__main__":
    fix_init_file()
