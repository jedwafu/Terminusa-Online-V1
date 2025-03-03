"""
Hunter Shop system for Terminusa Online
"""
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
from models import db, User, Item, Transaction, Wallet
from game_config import (
    INVENTORY_EXPANSION_SIZE,
    INVENTORY_EXPANSION_COST,
    RENAME_LICENSE_COST,
    JOB_RESET_COST,
    JOB_LICENSE_COST,
    HUNTER_CLASS_UPGRADE_COST,
    REMOTE_SHOP_LICENSE_COST,
    BASIC_RESURRECTION_COST,
    HIGHER_RESURRECTION_COST
)

class HunterShop:
    """Handles the Hunter Shop system with special items and licenses"""

    SHOP_ITEMS = {
        # Inventory Management
        'inventory_expansion': {
            'name': 'Inventory Expansion',
            'description': 'Expand inventory by 10 slots',
            'cost': INVENTORY_EXPANSION_COST,
            'currency': 'crystals'
        },
        'rename_license': {
            'name': 'Rename License',
            'description': 'Allows changing character name',
            'cost': RENAME_LICENSE_COST,
            'currency': 'crystals'
        },
        
        # Job Related
        'job_reset': {
            'name': 'Job Reset License',
            'description': 'Reset job class and skills',
            'cost': JOB_RESET_COST,
            'currency': 'exons'
        },
        'job_license': {
            'name': 'Job License',
            'description': 'Required for job class changes',
            'cost': JOB_LICENSE_COST,
            'currency': 'exons'
        },
        'hunter_class_upgrade': {
            'name': 'Hunter Class Upgrade License',
            'description': 'Required for hunter class promotion',
            'cost': HUNTER_CLASS_UPGRADE_COST,
            'currency': 'exons'
        },
        
        # Shop Licenses
        'remote_shop_basic': {
            'name': 'Remote Shop License (Basic)',
            'description': 'Access basic shop features remotely',
            'cost': REMOTE_SHOP_LICENSE_COST,
            'currency': 'exons'
        },
        'remote_shop_advanced': {
            'name': 'Remote Shop License (Advanced)',
            'description': 'Access advanced shop features remotely',
            'cost': REMOTE_SHOP_LICENSE_COST * 2,
            'currency': 'exons'
        },
        
        # Resurrection Items
        'basic_resurrection': {
            'name': 'Basic Resurrection Potion',
            'description': 'Revive with 50% HP',
            'cost': BASIC_RESURRECTION_COST,
            'currency': 'exons'
        },
        'higher_resurrection': {
            'name': 'Higher Resurrection Potion',
            'description': 'Revive with 100% HP, works on decapitated',
            'cost': HIGHER_RESURRECTION_COST,
            'currency': 'exons'
        },
        
        # Potions and Antidotes
        'life_potion_high': {
            'name': 'High-Grade Life Potion',
            'description': 'Restore 75% HP',
            'cost': 100,
            'currency': 'crystals'
        },
        'mana_potion_high': {
            'name': 'High-Grade Mana Potion',
            'description': 'Restore 75% MP',
            'cost': 100,
            'currency': 'crystals'
        },
        'chill_antidote': {
            'name': 'Chill Antidote',
            'description': 'Cures burn status',
            'cost': 50,
            'currency': 'crystals'
        },
        'cleansing_antidote': {
            'name': 'Cleansing Antidote',
            'description': 'Cures poison status',
            'cost': 50,
            'currency': 'crystals'
        },
        'flame_antidote': {
            'name': 'Flame Antidote',
            'description': 'Cures frozen status',
            'cost': 50,
            'currency': 'crystals'
        },
        'shilajit_antidote': {
            'name': 'Shilajit Antidote',
            'description': 'Cures fear and confusion',
            'cost': 75,
            'currency': 'crystals'
        }
    }

    def __init__(self):
        self._admin_wallet = None

    @property
    def admin_wallet(self):
        """Lazy load admin wallet"""
        if self._admin_wallet is None:
            self._admin_wallet = Wallet.query.filter_by(
                solana_address='FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw'
            ).first()
        return self._admin_wallet

    def get_shop_items(self, user: User) -> Dict:
        """Get available shop items for user"""
        items = {}
        for item_id, item in self.SHOP_ITEMS.items():
            # Check if user meets requirements for item
            if self._check_item_requirements(user, item_id):
                items[item_id] = item
        return items

    def purchase_item(self, user: User, item_id: str, quantity: int = 1) -> Dict:
        """Purchase item from the Hunter Shop"""
        if item_id not in self.SHOP_ITEMS:
            return {
                "success": False,
                "message": "Invalid item"
            }

        item = self.SHOP_ITEMS[item_id]
        total_cost = item['cost'] * quantity

        # Check if user has enough currency
        wallet = Wallet.query.filter_by(user_id=user.id).first()
        if not wallet:
            return {
                "success": False,
                "message": "User wallet not found"
            }

        if not self._check_balance(wallet, item['currency'], total_cost):
            return {
                "success": False,
                "message": f"Insufficient {item['currency']}"
            }

        try:
            # Process special items
            if item_id == 'inventory_expansion':
                result = self._process_inventory_expansion(user)
            elif item_id == 'rename_license':
                result = self._process_rename_license(user)
            elif item_id == 'job_reset':
                result = self._process_job_reset(user)
            elif item_id == 'job_license':
                result = self._process_job_license(user)
            elif item_id == 'hunter_class_upgrade':
                result = self._process_hunter_upgrade(user)
            elif item_id.startswith('remote_shop'):
                result = self._process_remote_shop(user, item_id)
            else:
                # Regular item purchase
                result = self._process_regular_item(user, item_id, quantity)

            if not result['success']:
                return result

            # Process payment
            if not self._process_payment(wallet, item['currency'], total_cost):
                return {
                    "success": False,
                    "message": "Payment processing failed"
                }

            # Record transaction
            transaction = Transaction(
                wallet_id=wallet.id,
                type="shop_purchase",
                currency=item['currency'],
                amount=total_cost,
                metadata={
                    "item_id": item_id,
                    "quantity": quantity
                }
            )
            db.session.add(transaction)
            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully purchased {quantity}x {item['name']}",
                "cost": str(total_cost),
                "currency": item['currency']
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Purchase failed: {str(e)}"
            }

    def _check_balance(self, wallet: Wallet, currency: str, amount: Decimal) -> bool:
        """Check if wallet has sufficient balance"""
        if currency == "crystals":
            return wallet.crystals_balance >= amount
        elif currency == "exons":
            return wallet.exons_balance >= amount
        return False

    def _process_payment(self, wallet: Wallet, currency: str, amount: Decimal) -> bool:
        """Process payment and transfer to admin wallet"""
        try:
            # Deduct from user
            if currency == "crystals":
                wallet.crystals_balance -= int(amount)
                self.admin_wallet.crystals_balance += int(amount)
            elif currency == "exons":
                wallet.exons_balance -= amount
                self.admin_wallet.exons_balance += amount

            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def _check_item_requirements(self, user: User, item_id: str) -> bool:
        """Check if user meets requirements for item"""
        # Add specific requirements checks here
        return True

    def _process_inventory_expansion(self, user: User) -> Dict:
        """Process inventory expansion purchase"""
        try:
            user.inventory_size += INVENTORY_EXPANSION_SIZE
            db.session.commit()
            return {
                "success": True,
                "message": f"Inventory expanded by {INVENTORY_EXPANSION_SIZE} slots"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to expand inventory: {str(e)}"
            }

    def _process_rename_license(self, user: User) -> Dict:
        """Process rename license purchase"""
        try:
            user.rename_licenses += 1
            db.session.commit()
            return {
                "success": True,
                "message": "Rename license added"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add rename license: {str(e)}"
            }

    def _process_job_reset(self, user: User) -> Dict:
        """Process job reset purchase"""
        try:
            user.job_reset_licenses += 1
            db.session.commit()
            return {
                "success": True,
                "message": "Job reset license added"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add job reset license: {str(e)}"
            }

    def _process_job_license(self, user: User) -> Dict:
        """Process job license purchase"""
        try:
            user.job_licenses += 1
            db.session.commit()
            return {
                "success": True,
                "message": "Job license added"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add job license: {str(e)}"
            }

    def _process_hunter_upgrade(self, user: User) -> Dict:
        """Process hunter class upgrade purchase"""
        try:
            user.hunter_upgrade_licenses += 1
            db.session.commit()
            return {
                "success": True,
                "message": "Hunter class upgrade license added"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add hunter upgrade license: {str(e)}"
            }

    def _process_remote_shop(self, user: User, license_type: str) -> Dict:
        """Process remote shop license purchase"""
        try:
            if license_type == 'remote_shop_basic':
                user.has_basic_remote_shop = True
            else:  # advanced
                user.has_advanced_remote_shop = True
            db.session.commit()
            return {
                "success": True,
                "message": f"{license_type.replace('_', ' ').title()} license added"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add remote shop license: {str(e)}"
            }

    def _process_regular_item(self, user: User, item_id: str, quantity: int) -> Dict:
        """Process regular item purchase"""
        try:
            # Add to user's inventory
            inventory_item = next(
                (item for item in user.inventory_items if item.item_id == item_id),
                None
            )
            
            if inventory_item:
                inventory_item.quantity += quantity
            else:
                inventory_item = Item(
                    user_id=user.id,
                    item_id=item_id,
                    quantity=quantity
                )
                db.session.add(inventory_item)
            
            db.session.commit()
            return {
                "success": True,
                "message": f"Added {quantity}x {self.SHOP_ITEMS[item_id]['name']} to inventory"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add item to inventory: {str(e)}"
            }
