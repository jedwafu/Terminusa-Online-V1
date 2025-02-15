import os
import sys
import subprocess
import requests
from getpass import getpass
import json
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
import base58
import hashlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from Crypto.Util.Padding import pad, unpad
from dotenv import load_dotenv
import time

from admin_dashboard import AdminDashboard

# Check and install dependencies
required_packages = ['requests', 'solders~=0.2.0', 'solana~=0.25.0']

def install_dependencies():
    print("[DEBUG] Checking required packages")
    for package in required_packages:
        try:
            print(f"[DEBUG] Checking package: {package}")
            __import__(package.split('~=')[0])
            print(f"[DEBUG] Package {package} is already installed")
        except ImportError:
            print(f"[DEBUG] Package {package} not found, installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"[DEBUG] Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"[DEBUG] Failed to install {package}: {str(e)}")
                sys.exit(1)
    print("[DEBUG] All required packages are installed")

install_dependencies()

BASE_URL = os.getenv('API_URL', 'http://46.250.228.210:5000')
SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
ADMIN_FILE = 'admin_status.json'

class GameClient:
    def __init__(self):
        print("[DEBUG] Initializing Game Client")
        print(f"[DEBUG] Using Solana RPC URL: {SOLANA_RPC_URL}")
        print(f"[DEBUG] Using API URL: {BASE_URL}")
        
        self.token = None
        self.current_user = None
        self.user_role = None
        self.base_url = BASE_URL
        
        print("[DEBUG] Initializing Solana client")
        try:
            self.solana_client = Client(SOLANA_RPC_URL)
            print("[DEBUG] Solana client initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Failed to initialize Solana client: {str(e)}")
            raise
        
        print("[DEBUG] Initializing inventory")
        self.inventory = {
            'weapons': [],
            'armor': [],
            'potions': 0,
            'level': 1,
            'experience': 0
        }
        print("[DEBUG] Inventory initialized")
        
        print("[DEBUG] Checking admin status")
        self.admin_exists = self._check_admin_exists()
        print("[DEBUG] Game Client initialization complete")

    def _check_admin_exists(self):
        print("[DEBUG] Checking if admin account exists")
        try:
            with open(ADMIN_FILE, 'r') as f:
                data = json.load(f)
                exists = data.get('admin_exists', False)
                print(f"[DEBUG] Admin exists: {exists}")
                return exists
        except FileNotFoundError:
            print("[DEBUG] Admin status file not found")
            return False
        except json.JSONDecodeError:
            print("[DEBUG] Admin status file is corrupted")
            return False

    def _set_admin_exists(self):
        print("[DEBUG] Setting admin account status")
        try:
            with open(ADMIN_FILE, 'w') as f:
                json.dump({'admin_exists': True}, f)
            print("[DEBUG] Admin status set successfully")
        except IOError as e:
            print(f"[DEBUG] Failed to set admin status: {str(e)}")

    def display_header(self, title):
        print("\n" + "=" * 50)
        print(f"{title:^50}")
        print("=" * 50)

    def display_message(self, message, type='info'):
        prefix = {
            'success': '[SUCCESS]',
            'error': '[ERROR]',
            'warning': '[WARNING]',
            'info': '[INFO]',
            'debug': '[DEBUG]'
        }
        print(f"\n{prefix.get(type, '[INFO]')} {message}")

    def login(self):
        self.display_header("Login")
        print("[DEBUG] Starting login process")
        
        # Input validation
        username = input("Username: ").strip()
        if not username:
            self.display_message("Username cannot be empty", 'error')
            return False
        print(f"[DEBUG] Username entered: {username}")
        
        password = getpass("Password: ")
        if not password:
            self.display_message("Password cannot be empty", 'error')
            return False
        print("[DEBUG] Password entered")
        
        try:
            # Prepare request data
            request_data = {
                'username': username,
                'password': password
            }
            print(f"[DEBUG] Sending login request for user: {username}")
            print(f"[DEBUG] Request URL: {BASE_URL}/login")
            
            # Send request
            response = requests.post(
                f"{BASE_URL}/login",
                json=request_data,
                timeout=10
            )
            
            success, result, error_msg = self._handle_response(response, "Login")
            if success:
                self.token = result.get('token')
                self.current_user = username
                self.user_role = result.get('role')  # Get role from response
                print(f"[DEBUG] Login successful - Role: {self.user_role}")
                
                # Get user data
                user_data = result.get('user', {})
                print(f"[DEBUG] User data: {user_data}")
                
                wallet_data = result.get('wallet', {})
                print(f"[DEBUG] Loading wallet data: {wallet_data}")
                self._load_user_data(wallet_data)
                
                if self.user_role == 'admin':
                    self.display_message(f"Welcome back, Admin {username}!", 'success')
                    print("[DEBUG] Admin user detected, will enter admin dashboard")
                else:
                    self.display_message(f"Welcome back, {username}!", 'success')
                    print("[DEBUG] Regular user detected, will enter game menu")
                return True
            else:
                error_details = error_msg or "Unknown error occurred"
                print(f"[DEBUG] Login failed - Details: {error_details}")
                self.display_message(f"Login failed: {error_details}", 'error')
                return False
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Network error during login: {str(e)}")
            self.display_message(f"Login failed: {str(e)}", 'error')
            return False
        except Exception as e:
            print(f"[DEBUG] Unexpected error during login: {str(e)}")
            self.display_message("An unexpected error occurred", 'error')
            return False

    def register(self):
        self.display_header("Register")
        print("[DEBUG] Starting registration process")
        
        # Username validation
        while True:
            username = input("Username: ").strip()
            if not username:
                self.display_message("Username cannot be empty", 'error')
                continue
            if not username.isalnum():
                self.display_message("Username must be alphanumeric", 'error')
                continue
            if len(username) < 3:
                self.display_message("Username must be at least 3 characters long", 'error')
                continue
            print(f"[DEBUG] Username validation passed: {username}")
            break
        
        # Password validation
        while True:
            password = getpass("Password: ")
            if len(password) < 8:
                self.display_message("Password must be at least 8 characters long", 'error')
                continue
            if not any(c.isupper() for c in password):
                self.display_message("Password must contain at least one uppercase letter", 'error')
                continue
            if not any(c.islower() for c in password):
                self.display_message("Password must contain at least one lowercase letter", 'error')
                continue
            if not any(c.isdigit() for c in password):
                self.display_message("Password must contain at least one number", 'error')
                continue
                
            confirm_password = getpass("Confirm Password: ")
            if password != confirm_password:
                self.display_message("Passwords do not match", 'error')
                continue
            print("[DEBUG] Password validation passed")
            break

        # Role selection
        role = 'user'
        if not self.admin_exists:
            print("\nNo admin account exists. Would you like to create an admin account?")
            is_admin = input("Create admin account? (y/n): ").lower() == 'y'
            if is_admin:
                role = 'admin'
        print(f"[DEBUG] Role selected: {role}")

        try:
            # Prepare request data
            request_data = {
                'username': username,
                'password': password,
                'role': role
            }
            print("[DEBUG] Sending registration request")
            print(f"[DEBUG] Request URL: {BASE_URL}/register")
            print(f"[DEBUG] Request data: {{'username': '{username}', 'role': '{role}'}}")
            
            # Send request
            response = requests.post(
                f"{BASE_URL}/register",
                json=request_data,
                timeout=10
            )
            
            success, result, error_msg = self._handle_response(response, "Registration")
            if success:
                if role == 'admin':
                    self._set_admin_exists()
                    print("[DEBUG] Admin status set successfully")
                    self.display_message("Admin account created successfully", 'success')
                else:
                    self.display_message("User account created successfully", 'success')
                return True
            else:
                error_details = error_msg or "Unknown error occurred"
                print(f"[DEBUG] Registration failed - Details: {error_details}")
                self.display_message(f"Registration failed: {error_details}", 'error')
                return False
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Network error during registration: {str(e)}")
            self.display_message(f"Connection error: {str(e)}", 'error')
            return False
        except Exception as e:
            print(f"[DEBUG] Unexpected error during registration: {str(e)}")
            self.display_message("An unexpected error occurred", 'error')
            return False

    def _handle_response(self, response, operation_name="Operation"):
        """
        Generic response handler with detailed debug logging
        Args:
            response: The response object from requests
            operation_name: Name of the operation for debug messages
        Returns:
            tuple: (success, result, error_message)
        """
        print(f"[DEBUG] Handling response for {operation_name}")
        print(f"[DEBUG] Response status code: {response.status_code}")
        print(f"[DEBUG] Response content: {response.text}")
        
        try:
            result = response.json()
            print(f"[DEBUG] Parsed response: {result}")
            
            if response.status_code == 200 and result.get('status') == 'success':
                print(f"[DEBUG] {operation_name} successful")
                return True, result, None
            else:
                error_msg = result.get('message', 'Unknown error')
                print(f"[DEBUG] {operation_name} failed with message: {error_msg}")
                if 'error' in result:
                    print(f"[DEBUG] Additional error details: {result['error']}")
                return False, result, error_msg
                
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse response JSON: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            return False, None, error_msg

    def _load_user_data(self, wallet_data):
        print("[DEBUG] Loading user wallet data")
        try:
            print(f"[DEBUG] Received wallet data: {wallet_data}")
            
            # Extract wallet data
            balance = wallet_data.get('balance', 0)
            crystals = wallet_data.get('assets', {}).get('crystals', 0)
            exons = wallet_data.get('assets', {}).get('exons', 0)
            
            print("[DEBUG] Extracted values:")
            print(f"[DEBUG] └── Balance: {balance} SOL")
            print(f"[DEBUG] └── Crystals: {crystals}")
            print(f"[DEBUG] └── Exons: {exons}")
            
            # Update inventory
            old_state = dict(self.inventory)
            self.inventory.update({
                'sol_balance': balance,
                'crystals': crystals,
                'exons': exons
            })
            
            # Log changes
            print("[DEBUG] Inventory state changes:")
            for key in ['sol_balance', 'crystals', 'exons']:
                old_val = old_state.get(key, 0)
                new_val = self.inventory[key]
                if old_val != new_val:
                    print(f"[DEBUG] └── {key}: {old_val} -> {new_val}")
                
            print("[DEBUG] Wallet data loaded successfully")
        except Exception as e:
            print(f"[DEBUG] Error loading wallet data: {str(e)}")
            raise

    def admin_dashboard(self):
        """Launch the admin dashboard"""
        print("[DEBUG] Initializing admin dashboard")
        dashboard = AdminDashboard(self)
        dashboard.run()

    def game_menu(self):
        """Regular user game menu"""
        print("[DEBUG] Entering game menu")
        try:
            while True:
                print("[DEBUG] Loading player data")
                
                # Get player stats for display
                balance = self.inventory.get('sol_balance', 0)
                level = self.inventory['level']
                experience = self.inventory['experience']
                exp_needed = 1000
                exp_progress = (experience / exp_needed) * 100
                
                print("[DEBUG] Current player state:")
                print(f"[DEBUG] SOL Balance: {balance:.4f}")
                print(f"[DEBUG] Level: {level}")
                print(f"[DEBUG] Experience: {experience}/{exp_needed} ({exp_progress:.1f}%)")
                
                # Display game menu
                self.display_header("Game Menu")
                print("\nPlayer Status:")
                print(f"└── Level: {level} ({exp_progress:.1f}% to next)")
                print(f"└── Balance: {balance:.4f} SOL")
                
                print("\nAvailable Actions:")
                print("└── 1. View Wallet")
                print("└── 2. View Inventory")
                print("└── 3. Logout")
                
                choice = input("\nSelect option: ")
                print(f"[DEBUG] User selected game option: {choice}")
                
                if choice == '1':
                    print("[DEBUG] Opening wallet view")
                    self._view_wallet()
                elif choice == '2':
                    print("[DEBUG] Opening inventory")
                    self._view_inventory()
                elif choice == '3':
                    print("[DEBUG] User logging out")
                    break
                else:
                    print(f"[DEBUG] Invalid game menu option: {choice}")
                    self.display_message("Invalid option", 'warning')
        except Exception as e:
            print(f"[DEBUG] Error in game menu: {str(e)}")
            self.display_message("An error occurred in the game menu", 'error')
        finally:
            print("[DEBUG] Exiting game menu")

    def _view_wallet(self):
        print("[DEBUG] Opening wallet view")
        try:
            self.display_header("Wallet Details")
            
            # Get wallet details
            balance = self.inventory.get('sol_balance', 0)
            crystals = self.inventory.get('crystals', 0)
            exons = self.inventory.get('exons', 0)
            
            print("[DEBUG] Current wallet state:")
            print(f"[DEBUG] SOL Balance: {balance:.4f} SOL")
            print(f"[DEBUG] Crystals: {crystals}")
            print(f"[DEBUG] Exons: {exons}")
            
            # Display to user
            print("\nWallet Details:")
            print(f"└── SOL Balance: {balance:.4f} SOL")
            print(f"└── Crystals: {crystals}")
            print(f"└── Exons: {exons}")
            
            input("\nPress Enter to continue...")
        except Exception as e:
            print(f"[DEBUG] Error displaying wallet: {str(e)}")
            self.display_message("An error occurred while viewing wallet", 'error')
        finally:
            print("[DEBUG] Closing wallet view")

    def _view_inventory(self):
        print("[DEBUG] Opening inventory view")
        try:
            self.display_header("Inventory")
            print("[DEBUG] Loading inventory data")
            
            # Get inventory details
            weapons = self.inventory['weapons']
            armor = self.inventory['armor']
            potions = self.inventory['potions']
            
            # Debug output
            print("[DEBUG] Current inventory state:")
            print(f"[DEBUG] Weapons count: {len(weapons)}")
            print(f"[DEBUG] Armor count: {len(armor)}")
            print(f"[DEBUG] Potions count: {potions}")
            print("[DEBUG] Full inventory state:", self.inventory)
            
            # Display to user
            print("\nInventory Contents:")
            print("└── Weapons:")
            if weapons:
                for weapon in weapons:
                    print(f"    └── {weapon}")
            else:
                print("    └── No weapons")
            
            print("└── Armor:")
            if armor:
                for item in armor:
                    print(f"    └── {item}")
            else:
                print("    └── No armor")
            
            print("└── Consumables:")
            print(f"    └── Potions: {potions}")
            
            input("\nPress Enter to continue...")
        except Exception as e:
            print(f"[DEBUG] Error displaying inventory: {str(e)}")
            self.display_message("An error occurred while viewing inventory", 'error')
        finally:
            print("[DEBUG] Closing inventory view")

    def run(self):
        print("[DEBUG] Starting game client")
        try:
            while True:
                print("[DEBUG] Loading system state")
                
                # Check admin status
                admin_exists = self._check_admin_exists()
                print(f"[DEBUG] Admin account exists: {admin_exists}")
                
                # Display welcome screen
                self.display_header("Welcome to Solo Leveling")
                print("\nSystem Status:")
                print("└── Admin Account:", "Configured" if admin_exists else "Not Configured")
                print("└── Server:", BASE_URL)
                
                print("\nAvailable Actions:")
                if not admin_exists:
                    print("└── First Time Setup:")
                    print("    └── 2. Create Admin Account")
                print("└── Account Access:")
                print("    └── 1. Login")
                if admin_exists:
                    print("    └── 2. Register New Account")
                print("└── System:")
                print("    └── 3. Exit")
                
                choice = input("\nSelect option: ")
                print(f"[DEBUG] User selected option: {choice}")
                
                if choice == '1':
                    print("[DEBUG] Processing login option")
                    if self.login():
                        if self.user_role == 'admin':
                            print("[DEBUG] Admin user detected, entering admin dashboard")
                            self.admin_dashboard()
                        else:
                            print("[DEBUG] Regular user detected, entering game menu")
                            self.game_menu()
                elif choice == '2':
                    print("[DEBUG] Processing registration option")
                    self.register()
                elif choice == '3':
                    print("[DEBUG] User requested exit")
                    self.display_message("Thank you for playing!", 'info')
                    break
                else:
                    print(f"[DEBUG] Invalid option selected: {choice}")
                    self.display_message("Invalid option", 'warning')
        except Exception as e:
            print(f"[DEBUG] Unexpected error in main loop: {str(e)}")
            self.display_message("An unexpected error occurred", 'error')
        finally:
            print("[DEBUG] Game client shutting down")

if __name__ == "__main__":
    client = GameClient()
    client.run()
