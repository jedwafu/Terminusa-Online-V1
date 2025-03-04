# Read the current content of models/__init__.py
with open('models/__init__.py', 'r') as f:
    content = f.read()

# Replace the relationship definition
new_content = content.replace(
    "    User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')",
    "    # Removed relationship to avoid circular imports\n    # User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')"
)

# Write the modified content back to models/__init__.py
with open('models/__init__.py', 'w') as f:
    f.write(new_content)

print("Successfully modified models/__init__.py")
