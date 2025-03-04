# Read the current content of models/announcement.py
with open('models/announcement.py', 'r') as f:
    content = f.read()

# Replace the relationship definition
new_content = content.replace(
    "author = relationship('User', foreign_keys=[author_id], backref=backref('authored_announcements', lazy='dynamic'))",
    "# Use string for relationship to avoid circular imports\nauthor = relationship('models.user.User', foreign_keys=[author_id], backref=backref('authored_announcements', lazy='dynamic'))"
)

# Write the modified content back to models/announcement.py
with open('models/announcement.py', 'w') as f:
    f.write(new_content)

print("Successfully modified models/announcement.py")
