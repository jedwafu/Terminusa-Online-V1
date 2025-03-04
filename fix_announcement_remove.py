# Read the current content of models/announcement.py
with open('models/announcement.py', 'r') as f:
    content = f.read()

# Replace the relationship definition
new_content = content.replace(
    "    # Author relationship\n    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)\n    # Defer the relationship to avoid circular imports\n    @property\n    def author(self):\n        from models.user import User\n        return User.query.get(self.author_id)",
    "    # Author relationship\n    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)"
)

# Write the modified content back to models/announcement.py
with open('models/announcement.py', 'w') as f:
    f.write(new_content)

print("Successfully modified models/announcement.py")
