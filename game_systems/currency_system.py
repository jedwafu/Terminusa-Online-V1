from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CurrencySystem:
    def __init__(self):
        self.logger = logger
        self.logger.info("Initializing Currency System")
        self.currencies = {
            'SOLANA': {
                'decimals': 9,
                'min_amount': 0.000000001,
                'max_transfer': 1000.0
            },
            'EXON': {
                'decimals': 0,
                'min_amount': 1,
                'max_transfer': 1000000
            },
            'CRYSTAL': {
                'decimals': 0,
                'min_amount': 1,
                'max_transfer': 1000000
            }
        }

    def validate_amount(self, currency: str, amount: float) -> Tuple[bool, str]:
        """Validate if an amount is valid for a given currency"""
        try:
            if currency not in self.currencies:
                return False, f"Invalid currency: {currency}"

            currency_info = self.currencies[currency]
            
            # Check minimum amount
            if amount < currency_info['min_amount']:
                return False, f"Amount below minimum ({currency_info['min_amount']} {currency})"

            # Check maximum transfer
            if amount > currency_info['max_transfer']:
                return False, f"Amount above maximum transfer limit ({currency_info['max_transfer']} {currency})"

            return True, "Amount valid"
        except Exception as e:
            self.logger.error(f"Error validating amount: {str(e)}", exc_info=True)
            return False, "Internal error"

    def format_amount(self, currency: str, amount: float) -> str:
        """Format an amount according to currency decimals"""
        try:
            if currency not in self.currencies:
                raise ValueError(f"Invalid currency: {currency}")

            decimals = self.currencies[currency]['decimals']
            return f"{amount:.{decimals}f}"
        except Exception as e:
            self.logger.error(f"Error formatting amount: {str(e)}", exc_info=True)
            return str(amount)

    def calculate_fee(self, currency: str, amount: float) -> float:
        """Calculate transaction fee for a given amount"""
        try:
            if currency not in self.currencies:
                raise ValueError(f"Invalid currency: {currency}")

            # Base fee rates
            fee_rates = {
                'SOLANA': 0.01,  # 1%
                'EXON': 0.02,    # 2%
                'CRYSTAL': 0.03  # 3%
            }

            return amount * fee_rates[currency]
        except Exception as e:
            self.logger.error(f"Error calculating fee: {str(e)}", exc_info=True)
            return 0.0

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies"""
        try:
            if from_currency not in self.currencies or to_currency not in self.currencies:
                raise ValueError("Invalid currency pair")

            # Fixed exchange rates
            rates = {
                'SOLANA_EXON': 1000.0,    # 1 SOL = 1000 EXON
                'EXON_CRYSTAL': 10.0      # 1 EXON = 10 CRYSTAL
            }

            rate_key = f"{from_currency}_{to_currency}"
            if rate_key in rates:
                return rates[rate_key]
            
            reverse_key = f"{to_currency}_{from_currency}"
            if reverse_key in rates:
                return 1.0 / rates[reverse_key]

            return None
        except Exception as e:
            self.logger.error(f"Error getting exchange rate: {str(e)}", exc_info=True)
            return None

    def calculate_conversion(self, from_currency: str, to_currency: str, amount: float) -> Tuple[Optional[float], float]:
        """Calculate currency conversion including fees"""
        try:
            rate = self.get_exchange_rate(from_currency, to_currency)
            if rate is None:
                raise ValueError("No exchange rate available")

            # Calculate fee
            fee = self.calculate_fee(from_currency, amount)
            
            # Calculate conversion
            converted_amount = (amount - fee) * rate

            return converted_amount, fee
        except Exception as e:
            self.logger.error(f"Error calculating conversion: {str(e)}", exc_info=True)
            return None, 0.0
