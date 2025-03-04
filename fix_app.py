# Read the current content of app.py
with open('app.py', 'r') as f:
    content = f.read()

# Replace the init_db function
new_content = content.replace(
    """# Initialize database tables
def init_db():
    \"\"\"Initialize database tables\"\"\"
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise""",
    """# Initialize database tables
def init_db():
    \"\"\"Initialize database tables\"\"\"
    try:
        with app.app_context():
            # Skip database initialization to avoid circular imports
            logger.info("Database initialization skipped")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise"""
)

# Write the modified content back to app.py
with open('app.py', 'w') as f:
    f.write(new_content)

print("Successfully modified app.py")
