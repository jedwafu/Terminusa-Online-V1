from typing import Dict, Optional, Tuple
from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime, timedelta
from models import db, User, Wallet, Transaction, SwapTransaction, TaxConfig
from game_config import MAX_CRYSTAL_SUPPLY

# Configure logging
logger = logging.getLogger(__name__)

class CurrencySystem:
    def __init__(self):
        self._admin_user = None
        self._rate_limit_cache = {}  # For rate limiting transactions

    @property
    def admin_user(self):
        """Lazy load admin user when needed"""
        if self._admin_user is None:
            from flask import current_app
            with current_app.app_context():
                self._admin_user = User.query.filter_by(username='adminbb').first()
        return self._admin_user

    def swap_currency(self, user: User, from_currency: str, to_currency: str, amount: Decimal) -> Dict:
        """Swap between currencies"""
        # Check rate limit
        if self._is_rate_limited(user.id):
            logger.warning(f"Rate limit exceeded for user {user.id}")
            return {
                "success": False,
                "message": "Too many transactions. Please try again later."
            }

        if amount <= 0:
            return {
                "success": False,
                "message": "Amount must be greater than 0"
            }

        logger.info(f"User {user.id} attempting to swap {amount} {from_currency} to {to_currency}")

        # Check if user has enough balance
        balance_check, error = self._check_balance(user, from_currency, amount)
        if not balance_check:
            return {
                "success": False,
                "message": error or f"Insufficient {from_currency} balance"
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
        return {
            "success": False,
            "message": "Failed to process swap"
        }

    def transfer_currency(self, from_user: User, to_user: User, currency: str, amount: Decimal) -> Dict:
        """Transfer currency between users"""
        # Check rate limit
        if self._is_rate_limited(from_user.id):
            logger.warning(f"Rate limit exceeded for user {from_user.id}")
            return {
                "success": False,
                "message": "Too many transactions. Please try again later."
            }

        if amount <= 0:
            return {
                "success": False,
                "message": "Amount must be greater than 0"
            }

        logger.info(f"User {from_user.id} attempting to transfer {amount} {currency} to {to_user.id}")

        # Check if sender has enough balance
        balance_check, error = self._check_balance(from_user, currency, amount)
        if not balance_check:
            return {
                "success": False,
                "message": error or f"Insufficient {currency} balance"
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
        return {
            "success": False,
            "message": "Failed to process transfer"
        }

    def _check_balance(self, user: User, currency: str, amount: Decimal) -> Tuple[bool, Optional[str]]:
        """Check if user has sufficient balance and validate amount
        
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            amount = Decimal(str(amount))  # Ensure valid decimal
            if amount <= 0:
                return False, "Amount must be greater than 0"

            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if not wallet:
                return False, "Wallet not found"

            if currency == "solana":
                return wallet.solana_balance >= amount, None
            elif currency == "exons":
                return wallet.exons_balance >= amount, None
            elif currency == "crystals":
                if wallet.crystals_balance + amount > MAX_CRYSTAL_SUPPLY:
                    return False, "Exceeds maximum crystal supply"
                return wallet.crystals_balance >= amount, None
            return False, "Invalid currency"
        except InvalidOperation:
            return False, "Invalid amount format"

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
        tax_config = TaxConfig.query.filter_by(currency_type=currency).first()
        if not tax_config:
            return Decimal("0")

        base_rate = tax_config.base_tax

        # Add guild tax if applicable
        if user.guild_id:
            base_rate += tax_config.guild_tax

        return Decimal(str(base_rate))

    def _process_swap(self, user: User, from_currency: str, to_currency: str,
                     amount: Decimal, converted_amount: Decimal, tax_amount: Decimal) -> bool:
        """Process currency swap transaction"""
        try:
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if not wallet:
                return False

            # Deduct from source currency
            if from_currency == "solana":
                wallet.solana_balance -= amount
            elif from_currency == "exons":
                wallet.exons_balance -= amount
            else:  # crystals
                wallet.crystals_balance -= int(amount)

            # Add to target currency
            if to_currency == "solana":
                wallet.solana_balance += converted_amount
            elif to_currency == "exons":
                wallet.exons_balance += converted_amount
            else:  # crystals
                wallet.crystals_balance += int(converted_amount)

            # Process tax
            if not self._process_tax(from_currency, tax_amount):
                return False

            # Record swap transaction
            swap_transaction = SwapTransaction(
                wallet_id=wallet.id,
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                rate=converted_amount / amount,
                fee=tax_amount,
                status='completed'
            )
            db.session.add(swap_transaction)
            db.session.commit()

            return True
        except Exception as e:
            logger.error(f"Swap failed: {str(e)}")
            db.session.rollback()
            return False

    def _process_transfer(self, from_user: User, to_user: User, currency: str,
                         amount: Decimal, net_amount: Decimal, tax_amount: Decimal) -> bool:
        """Process currency transfer transaction"""
        try:
            from_wallet = Wallet.query.filter_by(user_id=from_user.id).first()
            to_wallet = Wallet.query.filter_by(user_id=to_user.id).first()
            if not from_wallet or not to_wallet:
                return False

            # Deduct from sender
            if currency == "solana":
                from_wallet.solana_balance -= amount
                to_wallet.solana_balance += net_amount
            elif currency == "exons":
                from_wallet.exons_balance -= amount
                to_wallet.exons_balance += net_amount
            else:  # crystals
                from_wallet.crystals_balance -= int(amount)
                to_wallet.crystals_balance += int(net_amount)

            # Process tax
            if not self._process_tax(currency, tax_amount):
                return False

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
        except Exception as e:
            logger.error(f"Transfer failed: {str(e)}")
            db.session.rollback()
            return False

    def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user has exceeded transaction rate limit
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user is rate limited
        """
        # Simple rate limiting - allow max 10 transactions per minute
        now = datetime.now()

        if user_id not in self._rate_limit_cache:
            self._rate_limit_cache[user_id] = []

        # Remove old transactions
        self._rate_limit_cache[user_id] = [
            t for t in self._rate_limit_cache[user_id]
            if now - t < timedelta(minutes=1)
        ]

        # Check if over limit
        if len(self._rate_limit_cache[user_id]) >= 10:
            return True

        # Record new transaction
        self._rate_limit_cache[user_id].append(now)
        return False

    def _process_tax(self, currency: str, amount: Decimal) -> bool:
        """Process tax payment to admin account
        
        Returns:
            bool: True if tax was processed successfully
        """
        logger.info(f"Processing tax: {amount} {currency}")
        try:
            tax_config = TaxConfig.query.filter_by(currency_type=currency).first()
            if not tax_config:
                return False

            admin_wallet = Wallet.query.filter_by(solana_address=tax_config.admin_wallet).first()
            if not admin_wallet:
                return False

            if currency == "solana":
                admin_wallet.solana_balance += amount
            elif currency == "exons":
                admin_wallet.exons_balance += amount
            else:  # crystals
                admin_wallet.crystals_balance += int(amount)

            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Tax processing failed: {str(e)}")
            db.session.rollback()
            return False
