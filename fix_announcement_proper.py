"""
Fix the circular dependency between User and Announcement models
"""

# Fix the Announcement model
with open('models/announcement.py', 'r') as f:
    content = f.read()

# Replace the relationship definition with a string-based one
new_content = content.replace(
    "author = relationship('User', foreign_keys=[author_id], backref=backref('authored_announcements', lazy='dynamic'))",
    "# Use string-based relationship to avoid circular imports\nauthor = relationship('models.user.User', foreign_keys=[author_id], backref=backref('authored_announcements', lazy='dynamic'))"
)

with open('models/announcement.py', 'w') as f:
    f.write(new_content)

# Fix the models/__init__.py file
with open('models/__init__.py', 'r') as f:
    content = f.read()

# Remove the duplicate relationship definition
new_content = content.replace(
    "    User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')",
    "    # Relationship defined in Announcement model\n    # User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')"
)

with open('models/__init__.py', 'w') as f:
    f.write(new_content)

print("Successfully fixed circular dependency between User and Announcement models")
