#!/usr/bin/env python3
"""Database management script for Terminusa Online"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import app, db
from models import *
from scripts.init_game_data import main as init_game_data

def backup_database(args):
    """Create a database backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = project_root / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / f'terminusa_db_backup_{timestamp}.sql'
    
    # Get database URL from config
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    db_name = db_url.split('/')[-1]
    
    # Create backup command
    cmd = f'pg_dump -U terminusa {db_name} > {backup_file}'
    
    print(f"Creating backup: {backup_file}")
    result = os.system(cmd)
    
    if result == 0:
        print("Backup created successfully!")
    else:
        print("Backup failed!")
        sys.exit(1)

def restore_database(args):
    """Restore database from backup"""
    backup_file = Path(args.file)
    if not backup_file.exists():
        print(f"Backup file not found: {backup_file}")
        sys.exit(1)
    
    # Get database URL from config
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    db_name = db_url.split('/')[-1]
    
    # Drop and recreate database
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
    
    # Restore from backup
    cmd = f'psql -U terminusa {db_name} < {backup_file}'
    
    print(f"Restoring from backup: {backup_file}")
    result = os.system(cmd)
    
    if result == 0:
        print("Database restored successfully!")
    else:
        print("Database restore failed!")
        sys.exit(1)

def reset_database(args):
    """Reset database to initial state"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        if not args.no_init:
            print("Initializing game data...")
            init_game_data()
        
        print("Database reset complete!")

def check_database(args):
    """Check database status and integrity"""
    with app.app_context():
        print("Checking database connection...")
        try:
            db.session.execute('SELECT 1')
            print("Database connection successful!")
        except Exception as e:
            print(f"Database connection failed: {e}")
            sys.exit(1)
        
        print("\nChecking tables...")
        tables = db.metadata.tables.keys()
        print(f"Found {len(tables)} tables:")
        for table in sorted(tables):
            try:
                count = db.session.execute(f'SELECT COUNT(*) FROM {table}').scalar()
                print(f"  - {table}: {count} rows")
            except Exception as e:
                print(f"  - {table}: ERROR - {e}")
        
        print("\nChecking enums...")
        enums = [
            'currency_type', 'hunter_class', 'base_job', 'health_status',
            'gate_grade', 'magic_beast_type', 'item_type', 'item_grade',
            'item_slot', 'guild_rank', 'quest_type', 'quest_status',
            'ai_model_type', 'player_activity_type'
        ]
        for enum in enums:
            try:
                db.session.execute(f"SELECT unnest(enum_range(NULL::{enum}))")
                print(f"  - {enum}: OK")
            except Exception as e:
                print(f"  - {enum}: ERROR - {e}")

def migrate_database(args):
    """Run database migrations"""
    from flask_migrate import upgrade, current, history
    
    with app.app_context():
        print("Current revision:", current())
        
        if args.info:
            print("\nMigration history:")
            history()
            return
        
        print("\nRunning migrations...")
        upgrade()
        
        print("\nNew revision:", current())
        print("Migrations complete!")

def main():
    parser = argparse.ArgumentParser(description="Terminusa Online Database Management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('file', help='Backup file to restore from')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database to initial state')
    reset_parser.add_argument('--no-init', action='store_true', 
                            help='Skip game data initialization')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check database status')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run database migrations')
    migrate_parser.add_argument('--info', action='store_true',
                              help='Show migration information')
    
    args = parser.parse_args()
    
    if args.command == 'backup':
        backup_database(args)
    elif args.command == 'restore':
        restore_database(args)
    elif args.command == 'reset':
        reset_database(args)
    elif args.command == 'check':
        check_database(args)
    elif args.command == 'migrate':
        migrate_database(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
