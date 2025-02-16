from typing import Dict, List, Optional
from datetime import datetime
import random
import logging
from .currency_system import CurrencySystem

logger = logging.getLogger(__name__)

class GachaPool:
    def __init__(self, id: str, name: str, description: str,
                 rates: Dict[str, float], price: float,
                 currency: str, items: Dict[str, Dict]):
        self.id = id
        self.name = name
        self.description = description
        self.rates = rates  # grade -> rate
        self.price = price
        self.currency = currency
        self.items = items  # grade -> list of possible items

class GachaSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.logger = logger
        self.logger.info("Initializing Gacha System")
        self.currency_system = currency_system
        self.pools: Dict[str, GachaPool] = self._initialize_pools()
        self.pull_history: List[Dict] = []
        self.pity_counters: Dict[str, Dict[int, int]] = {}  # pool_id -> user_id -> counter

    def _initialize_pools(self) -> Dict[str, GachaPool]:
        """Initialize default gacha pools"""
        return {
            'standard': GachaPool(
                id='standard',
                name='Standard Pool',
                description='Regular gacha pool with standard rates',
                rates={
                    'common': 0.60,
                    'uncommon': 0.30,
                    'rare': 0.08,
                    'epic': 0.015,
                    'legendary': 0.005
                },
                price=100,
                currency='CRYSTAL',
                items=self._get_standard_items()
            ),
            'premium': GachaPool(
                id='premium',
                name='Premium Pool',
                description='Premium pool with better rates',
                rates={
                    'uncommon': 0.45,
                    'rare': 0.35,
                    'epic': 0.15,
                    'legendary': 0.05
                },
                price=1000,
                currency='EXON',
                items=self._get_premium_items()
            )
        }

    def _get_standard_items(self) -> Dict[str, List[Dict]]:
        """Get standard pool items"""
        return {
            'common': [
                {'id': 'item1', 'name': 'Common Sword', 'type': 'weapon'},
                {'id': 'item2', 'name': 'Common Shield', 'type': 'armor'}
            ],
            'uncommon': [
                {'id': 'item3', 'name': 'Uncommon Sword', 'type': 'weapon'},
                {'id': 'item4', 'name': 'Uncommon Shield', 'type': 'armor'}
            ],
            'rare': [
                {'id': 'item5', 'name': 'Rare Sword', 'type': 'weapon'},
                {'id': 'item6', 'name': 'Rare Shield', 'type': 'armor'}
            ],
            'epic': [
                {'id': 'item7', 'name': 'Epic Sword', 'type': 'weapon'},
                {'id': 'item8', 'name': 'Epic Shield', 'type': 'armor'}
            ],
            'legendary': [
                {'id': 'item9', 'name': 'Legendary Sword', 'type': 'weapon'},
                {'id': 'item10', 'name': 'Legendary Shield', 'type': 'armor'}
            ]
        }

    def _get_premium_items(self) -> Dict[str, List[Dict]]:
        """Get premium pool items"""
        return {
            'uncommon': [
                {'id': 'item11', 'name': 'Premium Uncommon Sword', 'type': 'weapon'},
                {'id': 'item12', 'name': 'Premium Uncommon Shield', 'type': 'armor'}
            ],
            'rare': [
                {'id': 'item13', 'name': 'Premium Rare Sword', 'type': 'weapon'},
                {'id': 'item14', 'name': 'Premium Rare Shield', 'type': 'armor'}
            ],
            'epic': [
                {'id': 'item15', 'name': 'Premium Epic Sword', 'type': 'weapon'},
                {'id': 'item16', 'name': 'Premium Epic Shield', 'type': 'armor'}
            ],
            'legendary': [
                {'id': 'item17', 'name': 'Premium Legendary Sword', 'type': 'weapon'},
                {'id': 'item18', 'name': 'Premium Legendary Shield', 'type': 'armor'}
            ]
        }

    def get_available_pools(self) -> List[Dict]:
        """Get list of available gacha pools"""
        return [{
            'id': pool.id,
            'name': pool.name,
            'description': pool.description,
            'price': pool.price,
            'currency': pool.currency,
            'rates': pool.rates
        } for pool in self.pools.values()]

    def pull_gacha(self, user, pool_id: str, pulls: int = 1) -> Dict:
        """Perform gacha pulls"""
        try:
            # Validate pool exists
            pool = self.pools.get(pool_id)
            if not pool:
                return {'status': 'error', 'message': 'Pool not found'}

            # Calculate total cost
            total_cost = pool.price * pulls

            # Validate currency and amount
            valid, message = self.currency_system.validate_amount(
                pool.currency,
                total_cost
            )
            if not valid:
                return {'status': 'error', 'message': message}

            # Check if user can afford
            if not self._can_afford(user, pool.currency, total_cost):
                return {
                    'status': 'error',
                    'message': f'Insufficient funds ({total_cost} {pool.currency})'
                }

            # Process pulls
            results = []
            for _ in range(pulls):
                pull_result = self._process_single_pull(user, pool)
                results.append(pull_result)

            # Process transaction
            transaction_result = self._process_transaction(
                user,
                pool.currency,
                total_cost
            )
            if transaction_result['status'] != 'success':
                return transaction_result

            # Record pulls
            for result in results:
                self.pull_history.append({
                    'user_id': user.id,
                    'pool_id': pool_id,
                    'item_id': result['item']['id'],
                    'grade': result['grade'],
                    'timestamp': datetime.utcnow()
                })

            return {
                'status': 'success',
                'results': results,
                'transaction_id': transaction_result['transaction_id']
            }

        except Exception as e:
            self.logger.error(f"Error processing gacha pulls: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _process_single_pull(self, user, pool: GachaPool) -> Dict:
        """Process a single gacha pull"""
        # Initialize pity counter if needed
        if pool.id not in self.pity_counters:
            self.pity_counters[pool.id] = {}
        if user.id not in self.pity_counters[pool.id]:
            self.pity_counters[pool.id][user.id] = 0

        # Get adjusted rates based on pity
        rates = self._adjust_rates_for_pity(pool.rates, self.pity_counters[pool.id][user.id])

        # Determine grade
        grade = self._determine_grade(rates)

        # Reset or increment pity counter
        if grade in ['epic', 'legendary']:
            self.pity_counters[pool.id][user.id] = 0
        else:
            self.pity_counters[pool.id][user.id] += 1

        # Select random item of determined grade
        items = pool.items[grade]
        item = random.choice(items)

        return {
            'grade': grade,
            'item': item
        }

    def _adjust_rates_for_pity(self, base_rates: Dict[str, float],
                              pity_counter: int) -> Dict[str, float]:
        """Adjust rates based on pity counter"""
        adjusted_rates = base_rates.copy()

        # Every 10 pulls without epic/legendary increases their rates
        pity_bonus = min(0.1, (pity_counter // 10) * 0.02)  # Max 10% bonus
        if pity_bonus > 0:
            # Increase epic and legendary rates
            for grade in ['epic', 'legendary']:
                if grade in adjusted_rates:
                    adjusted_rates[grade] += pity_bonus

            # Decrease common rate to compensate
            if 'common' in adjusted_rates:
                adjusted_rates['common'] = max(0.1, adjusted_rates['common'] - pity_bonus * 2)

        # Normalize rates
        total = sum(adjusted_rates.values())
        return {grade: rate/total for grade, rate in adjusted_rates.items()}

    def _determine_grade(self, rates: Dict[str, float]) -> str:
        """Determine pull grade based on rates"""
        roll = random.random()
        cumulative = 0
        for grade, rate in rates.items():
            cumulative += rate
            if roll <= cumulative:
                return grade
        return list(rates.keys())[0]  # Fallback to first grade

    def get_pull_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's pull history"""
        try:
            user_history = [
                pull for pull in self.pull_history
                if pull['user_id'] == user_id
            ]
            return sorted(
                user_history,
                key=lambda x: x['timestamp'],
                reverse=True
            )[:limit]
        except Exception as e:
            self.logger.error(f"Error getting pull history: {str(e)}", exc_info=True)
            return []

    def _can_afford(self, user, currency: str, amount: float) -> bool:
        """Check if user can afford pulls"""
        # TODO: Implement actual balance check
        return True

    def _process_transaction(self, user, currency: str, amount: float) -> Dict:
        """Process the gacha transaction"""
        try:
            # TODO: Implement actual transaction processing
            return {
                'status': 'success',
                'transaction_id': f"tx_{datetime.utcnow().timestamp()}"
            }
        except Exception as e:
            self.logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Transaction failed'}
