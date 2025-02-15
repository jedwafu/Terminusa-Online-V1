import requests

class AdminDashboard:
    def __init__(self, client):
        self.client = client
        self.token = client.token
        self.base_url = client.base_url
        self.display_header = client.display_header
        self.display_message = client.display_message
        self._handle_response = client._handle_response

    def run(self):
        print("[DEBUG] Entering admin dashboard")
        try:
            while True:
                print("[DEBUG] Loading admin data")
                
                # Get system stats
                try:
                    headers = {'Authorization': f'Bearer {self.token}'}
                    print(f"[DEBUG] Using authorization token: {self.token[:20]}...")
                    print(f"[DEBUG] Making request to {self.base_url}/admin/users")
                    
                    users_response = requests.get(
                        f"{self.base_url}/admin/users",
                        headers=headers,
                        timeout=10
                    )
                    wallets_response = requests.get(
                        f"{self.base_url}/admin/wallets",
                        headers=headers,
                        timeout=10
                    )
                    
                    print(f"[DEBUG] Users response status: {users_response.status_code}")
                    print(f"[DEBUG] Users response content: {users_response.text}")
                    
                    users_success, users_result, _ = self._handle_response(users_response, "Get Users")
                    wallets_success, wallets_result, _ = self._handle_response(wallets_response, "Get Wallets")
                    
                    users_count = len(users_result.get('users', [])) if users_success else 0
                    wallets_count = len(wallets_result.get('wallets', [])) if wallets_success else 0
                    
                    print("[DEBUG] Current system state:")
                    print(f"[DEBUG] Total users: {users_count}")
                    print(f"[DEBUG] Total wallets: {wallets_count}")
                except Exception as e:
                    print("[DEBUG] Failed to fetch system stats")
                    print(f"[DEBUG] Error: {str(e)}")
                    users_count = wallets_count = "N/A"
                
                # Display admin dashboard
                self.display_header("Admin Dashboard")
                print("\nSystem Status:")
                print(f"└── Total Users: {users_count}")
                print(f"└── Total Wallets: {wallets_count}")
                
                print("\nAvailable Actions:")
                print("└── 1. View All Users")
                print("└── 2. View All Wallets")
                print("└── 3. Return to Main Menu")
                
                choice = input("\nSelect option: ")
                print(f"[DEBUG] Admin selected option: {choice}")
                
                if choice == '1':
                    print("[DEBUG] Accessing user list")
                    self._view_users()
                elif choice == '2':
                    print("[DEBUG] Accessing wallet list")
                    self._view_wallets()
                elif choice == '3':
                    print("[DEBUG] Returning to main menu")
                    break
                else:
                    print(f"[DEBUG] Invalid admin option: {choice}")
                    self.display_message("Invalid option", 'warning')
        except Exception as e:
            print(f"[DEBUG] Error in admin dashboard: {str(e)}")
            self.display_message("An error occurred in the admin dashboard", 'error')
        finally:
            print("[DEBUG] Exiting admin dashboard")

    def _view_users(self):
        print("[DEBUG] Fetching user list")
        try:
            print("[DEBUG] Sending request to /admin/users")
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"[DEBUG] Using authorization token: {self.token[:20]}...")
            
            response = requests.get(
                f"{self.base_url}/admin/users",
                headers=headers,
                timeout=10
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response content: {response.text}")
            
            success, result, error_msg = self._handle_response(response, "View Users")
            if success:
                self.display_header("User List")
                users = result.get('users', [])
                print(f"[DEBUG] Found {len(users)} users")
                
                for user in users:
                    print(f"\nID: {user['id']}")
                    print(f"Username: {user['username']}")
                    print(f"Role: {user['role']}")
                    print(f"Created: {user['created_at']}")
                    print("[DEBUG] User details:", user)
                
                input("\nPress Enter to continue...")
            else:
                self.display_message(f"Failed to fetch users: {error_msg}", 'error')
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Network error while fetching users: {str(e)}")
            self.display_message(f"Failed to fetch users: {str(e)}", 'error')
        except Exception as e:
            print(f"[DEBUG] Unexpected error in view_users: {str(e)}")
            self.display_message("An error occurred while viewing users", 'error')
        finally:
            print("[DEBUG] Completed user list operation")

    def _view_wallets(self):
        print("[DEBUG] Fetching wallet list")
        try:
            print("[DEBUG] Sending request to /admin/wallets")
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"[DEBUG] Using authorization token: {self.token[:20]}...")
            
            response = requests.get(
                f"{self.base_url}/admin/wallets",
                headers=headers,
                timeout=10
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response content: {response.text}")
            
            success, result, error_msg = self._handle_response(response, "View Wallets")
            if success:
                self.display_header("Wallet List")
                wallets = result.get('wallets', [])
                print(f"[DEBUG] Found {len(wallets)} wallets")
                
                for wallet in wallets:
                    print(f"\nUser ID: {wallet['user_id']}")
                    print(f"Address: {wallet['address']}")
                    print(f"Balance: {wallet['sol_balance']} SOL")
                    print(f"Crystals: {wallet['crystals']}")
                    print(f"Exons: {wallet['exons']}")
                    print("[DEBUG] Wallet details:", wallet)
                
                input("\nPress Enter to continue...")
            else:
                self.display_message(f"Failed to fetch wallets: {error_msg}", 'error')
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Network error while fetching wallets: {str(e)}")
            self.display_message(f"Failed to fetch wallets: {str(e)}", 'error')
        except Exception as e:
            print(f"[DEBUG] Unexpected error in view_wallets: {str(e)}")
            self.display_message("An error occurred while viewing wallets", 'error')
        finally:
            print("[DEBUG] Completed wallet list operation")
