#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from db_setup import DatabaseSetup
import sys
from app import app

def main():
    # Load environment variables
    load_dotenv()
    
    print("Starting database reset...")
    
    # Create database setup instance
    db_setup = DatabaseSetup(app)
    
    # Reset database
    print("Resetting database...")
    if not db_setup.reset_database():
        print("Error: Failed to reset database")
        sys.exit(1)
    
    # Verify database setup
    print("Verifying database setup...")
    if not db_setup.verify_database():
        print("Error: Database verification failed")
        sys.exit(1)
    
    print("\nTest accounts created:")
    print("1. Admin user:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Role: Administrator")
    print("   Level: 100")
    print("   Rank: S")
    print("\n2. Test users:")
    for i in range(1, 6):
        print(f"   User {i}:")
        print(f"   Username: test_user_{i}")
        print(f"   Password: password{i}")
        print(f"   Role: Player")
        print(f"   Level: 1")
        print(f"   Rank: F")
        print(f"   Starting Crystals: {os.getenv('STARTING_CRYSTALS', 20)}")
        print(f"   Starting Exons: {os.getenv('STARTING_EXONS', 0)}")
        print(f"   Inventory Slots: {os.getenv('STARTING_INVENTORY_SLOTS', 20)}")
        print()
    
    print("\nInitial Gates Created:")
    print("1. Training Ground")
    print("   - Level Requirement: 1")
    print("   - Rank Requirement: F")
    print("   - Type: Normal")
    print("\n2. Forest of Trials")
    print("   - Level Requirement: 5")
    print("   - Rank Requirement: F")
    print("   - Type: Elite")
    print("\n3. Demon's Lair")
    print("   - Level Requirement: 10")
    print("   - Rank Requirement: E")
    print("   - Type: Boss")
    
    print("\nDatabase reset completed successfully!")
    print("\nYou can now:")
    print("1. Start the server: python main.py")
    print("2. Run the CLI client: python client.py")
    print("3. Access the web interface: https://terminusa.online")
    print("4. Play through the CLI: python client.py")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
