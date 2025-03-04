"""
Fix the indentation issue in the Announcement model
"""

# Fix the Announcement model
with open('models/announcement.py', 'r') as f:
    content = f.read()

# Replace the relationship definition with a string-based one
new_content = content.replace(
    "    # Author relationship\n    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)\n    author = relationship('User', foreign_keys=[author_id], backref=backref('authored_announcements', lazy='dynamic'))\n\n\n    def __repr__(self):",
    "    # Author relationship\n    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)\n    # Use string-based relationship to avoid circular imports\n    author = relationship('models.user.User', foreign_keys=[author_id], backref=backref('authored_announcements', lazy='dynamic'))\n\n    def __repr__(self):"
)

with open('models/announcement.py', 'w') as f:
    f.write(new_content)

print("Successfully fixed indentation issue in Announcement model")
