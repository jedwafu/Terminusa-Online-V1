from typing import Dict, Optional
from decimal import Decimal
from models import db, User, Transaction
from game_config import (
    CRYSTAL_TAX_RATE, EXON_TAX_RATE, SOLANA_TAX_RATE,
    GUILD_CRYSTAL_TAX_RATE, GUILD_EXON_TAX_RATE,
    ADMIN_USERNAME, ADMIN_WALLET
)

class CurrencySystem:
    def __init__(self):
        self.admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
        
    def swap_currency(self, user: User, from_currency: str, to_currency: str, amount: Decimal) -> Dict:
        """Swap between currencies"""
        if amount <= 0:
            return {
                "success": False,
                "message": "Amount must be greater than 0"
            }
            
        # Check if user has enough balance
        if not self._check_balance(user, from_currency, amount):
            return {
                "success": False,
                "message": f"Insufficient {from_currency} balance"
            }
            
        # Calculate conversion rate and fees
        conversion_rate = self._get_conversion_rate(from_currency, to_currency)
        tax_rate = self._get_tax_rate(from_currency, user)
        
        # Calculate amounts
        tax_amount = amount * tax_rate
        net_amount = amount - tax_amount
        converted_amount = net_amount * conversion_rate
        
        # Process the swap
        if self._process_swap(user, from_currency, to_currency, amount, converted_amount, tax_amount):
            return {
                "success": True,
                "message": f"Swapped {amount} {from_currency} to {converted_amount} {to_currency}",
                "tax_paid": tax_amount,
                "received": converted_amount
            }
        else:
            return {
                "success": False,
                "message": "Failed to process swap"
            }

    def transfer_currency(self, from_user: User, to_user: User, currency: str, amount: Decimal) -> Dict:
        """Transfer currency between users"""
        if amount <= 0:
            return {
                "success": False,
                "message": "Amount must be greater than 0"
            }
            
        # Check if sender has enough balance
        if not self._check_balance(from_user, currency, amount):
            return {
                "success": False,
                "message": f"Insufficient {currency} balance"
            }
            
        # Calculate tax
        tax_rate = self._get_tax_rate(currency, from_user)
        tax_amount = amount * tax_rate
        net_amount = amount - tax_amount
        
        # Process the transfer
        if self._process_transfer(from_user, to_user, currency, amount, net_amount, tax_amount):
            return {
                "success": True,
                "message": f"Transferred {net_amount} {currency} to {to_user.username}",
                "tax_paid": tax_amount,
                "transferred": net_amount
            }
        else:
            return {
                "success": False,
                "message": "Failed to process transfer"
            }

    def _check_balance(self, user: User, currency: str, amount: Decimal) -> bool:
        """Check if user has sufficient balance"""
        if currency == "solana":
            return user.solana_balance >= amount
        elif currency == "exons":
            return user.exons_balance >= amount
        elif currency == "crystals":
            return user.crystals >= amount
        return False

    def _get_conversion_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Get current conversion rate between currencies"""
        # These rates should be fetched from an oracle or price feed in production
        rates = {
            "solana_to_exons": Decimal("100"),    # 1 SOL = 100 EXON
            "exons_to_crystals": Decimal("100"),  # 1 EXON = 100 CRYSTAL
            "solana_to_crystals": Decimal("10000")  # 1 SOL = 10000 CRYSTAL
        }
        
        if from_currency == "solana" and to_currency == "exons":
            return rates["solana_to_exons"]
        elif from_currency == "exons" and to_currency == "crystals":
            return rates["exons_to_crystals"]
        elif from_currency == "solana" and to_currency == "crystals":
            return rates["solana_to_crystals"]
        elif from_currency == "exons" and to_currency == "solana":
            return Decimal("1") / rates["solana_to_exons"]
        elif from_currency == "crystals" and to_currency == "exons":
            return Decimal("1") / rates["exons_to_crystals"]
        elif from_currency == "crystals" and to_currency == "solana":
            return Decimal("1") / rates["solana_to_crystals"]
            
        return Decimal("0")

    def _get_tax_rate(self, currency: str, user: User) -> Decimal:
        """Get tax rate for currency transaction"""
        base_rate = {
            "solana": SOLANA_TAX_RATE,
            "exons": EXON_TAX_RATE,
            "crystals": CRYSTAL_TAX_RATE
        }.get(currency, Decimal("0"))
        
        # Add guild tax if applicable
        if user.guild_id:
            guild_rate = {
                "exons": GUILD_EXON_TAX_RATE,
                "crystals": GUILD_CRYSTAL_TAX_RATE
            }.get(currency, Decimal("0"))
            base_rate += guild_rate
            
        return base_rate

    def _process_swap(self, user: User, from_currency: str, to_currency: str,
                     amount: Decimal, converted_amount: Decimal, tax_amount: Decimal) -> bool:
        """Process currency swap transaction"""
        try:
            # Deduct from source currency
            if from_currency == "solana":
                user.solana_balance -= amount
            elif from_currency == "exons":
                user.exons_balance -= amount
            else:  # crystals
                user.crystals -= int(amount)
                
            # Add to target currency
            if to_currency == "solana":
                user.solana_balance += converted_amount
            elif to_currency == "exons":
                user.exons_balance += converted_amount
            else:  # crystals
                user.crystals += int(converted_amount)
                
            # Process tax
            self._process_tax(from_currency, tax_amount)
            
            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type="swap",
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                converted_amount=converted_amount,
                tax_amount=tax_amount
            )
            db.session.add(transaction)
            db.session.commit()
            
            return True
        except Exception:
            db.session.rollback()
            return False

    def _process_transfer(self, from_user: User, to_user: User, currency: str,
                         amount: Decimal, net_amount: Decimal, tax_amount: Decimal) -> bool:
        """Process currency transfer transaction"""
        try:
            # Deduct from sender
            if currency == "solana":
                from_user.solana_balance -= amount
                to_user.solana_balance += net_amount
            elif currency == "exons":
                from_user.exons_balance -= amount
                to_user.exons_balance += net_amount
            else:  # crystals
                from_user.crystals -= int(amount)
                to_user.crystals += int(net_amount)
                
            # Process tax
            self._process_tax(currency, tax_amount)
            
            # Record transaction
            transaction = Transaction(
                user_id=from_user.id,
                recipient_id=to_user.id,
                type="transfer",
                currency=currency,
                amount=amount,
                net_amount=net_amount,
                tax_amount=tax_amount
            )
            db.session.add(transaction)
            db.session.commit()
            
            return True
        except Exception:
            db.session.rollback()
            return False

    def _process_tax(self, currency: str, amount: Decimal) -> None:
        """Process tax payment to admin account"""
        if currency == "solana":
            # Send to admin wallet
            # This should integrate with actual blockchain in production
            pass
        elif currency == "exons":
            # Send to admin wallet
            # This should integrate with actual blockchain in production
            pass
        else:  # crystals
            if self.admin_user:
                self.admin_user.crystals += int(amount)
