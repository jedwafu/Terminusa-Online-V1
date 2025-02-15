from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import random
import json

from ai_manager import AISystem
from combat_manager import CombatSystem
from economy_systems import CurrencySystem, MarketplaceSystem, ShopSystem, GachaSystem
from game_mechanics import JobSystem, SkillSystem, GateSystem, DurabilitySystem
from progression_manager import ProgressionManager

class AIBehaviorSystem:
    def __init__(self, ai_system: AISystem):
        self.ai_system = ai_system
        self.behavior_cache = {}
        self.cache_duration = 300  # 5 minutes

    def get_player_behavior(self, user_id: int, activity_history: List[Dict]) -> Dict:
        """Get or update player behavior analysis"""
        now = datetime.utcnow()
        
        # Check cache
        if user_id in self.behavior_cache:
            cached_time, cached_profile = self.behavior_cache[user_id]
            if (now - cached_time).total_seconds() < self.cache_duration:
                return cached_profile
        
        # Generate new profile
        profile = self.ai_system.analyze_player_behavior(user_id, activity_history)
        self.behavior_cache[user_id] = (now, profile)
        return profile

class LootSystem:
    def __init__(self, ai_system: AISystem):
        self.ai_system = ai_system
        self.base_drop_rates = {
            'normal': {
                'common': 0.7,
                'uncommon': 0.25,
                'rare': 0.05
            },
            'elite': {
                'common': 0.4,
                'uncommon': 0.4,
                'rare': 0.15,
                'epic': 0.05
            },
            'boss': {
                'uncommon': 0.3,
                'rare': 0.4,
                'epic': 0.25,
                'legendary': 0.05
            },
            'monarch': {
                'rare': 0.3,
                'epic': 0.4,
                'legendary': 0.25,
                'immortal': 0.05
            }
        }

    def calculate_drops(self, monster_type: str, player_luck: int, party_size: int) -> List[Dict]:
        """Calculate drops from a monster"""
        base_rates = self.base_drop_rates[monster_type]
        
        # Adjust rates based on luck
        luck_bonus = min(0.2, player_luck * 0.001)  # Max 20% bonus from luck
        adjusted_rates = {
            grade: min(1.0, rate * (1 + luck_bonus))
            for grade, rate in base_rates.items()
        }
        
        # Party size penalty (diminishing returns)
        if party_size > 1:
            party_penalty = 1 - (0.1 * (party_size - 1))  # 10% penalty per additional member
            party_penalty = max(0.5, party_penalty)  # Min 50% of original rates
            adjusted_rates = {
                grade: rate * party_penalty
                for grade, rate in adjusted_rates.items()
            }
        
        # Generate drops
        drops = []
        for grade, rate in adjusted_rates.items():
            if random.random() < rate:
                drops.append({
                    'grade': grade,
                    'type': self._generate_item_type(grade),
                    'stats': self._generate_item_stats(grade)
                })
        
        return drops

    def _generate_item_type(self, grade: str) -> str:
        """Generate a random item type based on grade"""
        types = ['weapon', 'armor', 'accessory', 'material']
        weights = {
            'common': [0.3, 0.3, 0.2, 0.2],
            'uncommon': [0.25, 0.25, 0.25, 0.25],
            'rare': [0.3, 0.3, 0.3, 0.1],
            'epic': [0.35, 0.35, 0.25, 0.05],
            'legendary': [0.4, 0.4, 0.2, 0],
            'immortal': [0.45, 0.45, 0.1, 0]
        }
        
        return random.choices(types, weights=weights[grade])[0]

    def _generate_item_stats(self, grade: str) -> Dict:
        """Generate item stats based on grade"""
        grade_multipliers = {
            'common': 1,
            'uncommon': 1.5,
            'rare': 2,
            'epic': 3,
            'legendary': 5,
            'immortal': 10
        }
        
        multiplier = grade_multipliers[grade]
        
        return {
            'attack': int(random.randint(5, 15) * multiplier),
            'defense': int(random.randint(5, 15) * multiplier),
            'hp': int(random.randint(10, 30) * multiplier),
            'mp': int(random.randint(10, 30) * multiplier),
            'durability': 100
        }

class TokenSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.currency_system = currency_system
        self.swap_rates = {
            'SOLANA_TO_EXON': 1000,  # 1 SOL = 1000 EXON
            'EXON_TO_CRYSTAL': 10    # 1 EXON = 10 CRYSTAL
        }
        self.min_swap_amounts = {
            'SOLANA': 0.1,           # Minimum 0.1 SOL
            'EXON': 100,            # Minimum 100 EXON
            'CRYSTAL': 1000         # Minimum 1000 CRYSTAL
        }

    def calculate_swap_amount(self, from_currency: str, to_currency: str, amount: float) -> Tuple[float, float]:
        """Calculate swap amount including fees"""
        if from_currency == 'SOLANA' and to_currency == 'EXON':
            rate = self.swap_rates['SOLANA_TO_EXON']
            result_amount = amount * rate
        elif from_currency == 'EXON' and to_currency == 'CRYSTAL':
            rate = self.swap_rates['EXON_TO_CRYSTAL']
            result_amount = amount * rate
        else:
            raise ValueError("Invalid currency pair")
        
        # Calculate fees
        fee = self.calculate_swap_fee(from_currency, amount)
        
        return result_amount, fee

    def calculate_swap_fee(self, currency: str, amount: float) -> float:
        """Calculate swap fee"""
        base_fee_rates = {
            'SOLANA': 0.01,  # 1%
            'EXON': 0.02,    # 2%
            'CRYSTAL': 0.03  # 3%
        }
        
        return amount * base_fee_rates[currency]

    def validate_swap(self, from_currency: str, amount: float) -> Tuple[bool, str]:
        """Validate if a swap is allowed"""
        if amount < self.min_swap_amounts.get(from_currency, 0):
            return False, f"Minimum swap amount is {self.min_swap_amounts[from_currency]} {from_currency}"
        
        return True, "Swap allowed"

class GameManager:
    def __init__(self):
        # Initialize core systems
        self.currency_system = CurrencySystem()
        self.ai_system = AISystem()
        
        # Initialize dependent systems
        self.job_system = JobSystem()
        self.skill_system = SkillSystem()
        self.gate_system = GateSystem()
        self.durability_system = DurabilitySystem()
        self.combat_system = CombatSystem(self.skill_system, self.durability_system)
        
        # Initialize economy systems
        self.marketplace_system = MarketplaceSystem(self.currency_system)
        self.shop_system = ShopSystem(self.currency_system)
        self.gacha_system = GachaSystem(self.currency_system)
        self.token_system = TokenSystem(self.currency_system)
        
        # Initialize progression and loot systems
        self.progression_manager = ProgressionManager()
        self.loot_system = LootSystem(self.ai_system)
        
        # Initialize behavior tracking
        self.ai_behavior = AIBehaviorSystem(self.ai_system)

    def process_gate_entry(self, user, gate, party_members: Optional[List] = None) -> Dict:
        """Process a gate entry request"""
        # Validate entry
        can_enter, message = self.gate_system.can_enter_gate(user, gate)
        if not can_enter:
            return {'status': 'error', 'message': message}
        
        # Get player behavior profile
        behavior = self.ai_behavior.get_player_behavior(user.id, user.activity_history)
        
        # Generate monsters with AI adjustment
        party_size = len(party_members) + 1 if party_members else 1
        monsters = self.gate_system.generate_gate_monsters(gate, party_size)
        monsters = self.ai_system.generate_gate_monsters(behavior, gate.grade, monsters)
        
        # Simulate combat
        if party_members:
            combat_result = self.combat_system.simulate_party_combat(
                [user] + party_members,
                monsters
            )
        else:
            combat_result = self.combat_system.simulate_solo_combat(user, monsters)
        
        # Process results
        processed_results = self.combat_system.process_combat_results(
            combat_result,
            [user] + (party_members or []),
            {}  # Equipment would be passed here
        )
        
        # Calculate and distribute rewards
        rewards = self.gate_system.calculate_rewards(gate, party_size, user.luck)
        rewards = self.ai_system.calculate_rewards(behavior, rewards)
        
        # Generate loot
        total_luck = user.luck + sum(member.luck for member in (party_members or []))
        loot = self.loot_system.calculate_drops(
            monster_type=monsters[-1]['type'],  # Use final monster's type
            player_luck=total_luck,
            party_size=party_size
        )
        
        return {
            'status': 'success',
            'combat_results': processed_results,
            'rewards': rewards,
            'loot': loot
        }

    def process_marketplace_action(self, action: str, user, **kwargs) -> Dict:
        """Process marketplace actions"""
        if action == 'create_listing':
            return self.marketplace_system.create_listing(
                seller=user,
                item_id=kwargs.get('item_id'),
                quantity=kwargs.get('quantity', 1),
                price=kwargs.get('price'),
                currency=kwargs.get('currency'),
                duration_days=kwargs.get('duration', 7)
            )
        elif action == 'purchase':
            return self.marketplace_system.purchase_listing(
                buyer=user,
                listing_id=kwargs.get('listing_id')
            )
        else:
            return {'status': 'error', 'message': 'Invalid marketplace action'}

    def process_token_swap(self, user, from_currency: str, to_currency: str, amount: float) -> Dict:
        """Process token swap requests"""
        # Validate swap
        valid, message = self.token_system.validate_swap(from_currency, amount)
        if not valid:
            return {'status': 'error', 'message': message}
        
        # Calculate swap amount and fees
        result_amount, fee = self.token_system.calculate_swap_amount(
            from_currency, to_currency, amount
        )
        
        # Process the swap (actual implementation would handle blockchain transactions)
        return {
            'status': 'success',
            'from_amount': amount,
            'to_amount': result_amount,
            'fee': fee,
            'from_currency': from_currency,
            'to_currency': to_currency
        }

    def process_gacha_pull(self, user, gacha_type: str, pulls: int = 1) -> Dict:
        """Process gacha pull requests"""
        # Get player behavior profile
        behavior = self.ai_behavior.get_player_behavior(user.id, user.activity_history)
        
        # Get base rates and adjust based on player profile
        base_rates = self.gacha_system.rates
        adjusted_rates = self.ai_system.adjust_gacha_rates(behavior, base_rates)
        
        # Perform pulls
        return self.gacha_system.pull_gacha(
            user=user,
            gacha_type=gacha_type,
            pulls=pulls
        )

    def process_achievement_update(self, user) -> List[Dict]:
        """Check and process achievement updates"""
        # Get current stats
        user_stats = {
            'gates_cleared': user.stats.get('gates_cleared', 0),
            'beasts_defeated': user.stats.get('beasts_defeated', 0),
            'bosses_defeated': user.stats.get('bosses_defeated', 0),
            'class_level': user.stats.get('class_level', 0),
            'class': user.job_class,
            'market_transactions': user.stats.get('market_transactions', 0),
            'crystals_earned': user.stats.get('crystals_earned', 0)
        }
        
        # Check for new achievements
        new_achievements = self.progression_manager.check_achievements(user_stats)
        
        # Process new achievements
        results = []
        for achievement in new_achievements:
            if achievement.id not in user.completed_achievements:
                # Apply achievement rewards
                user_data = self.progression_manager.apply_achievement_rewards(
                    user.__dict__,
                    achievement
                )
                
                # Update user object (actual implementation would update database)
                for key, value in user_data.items():
                    setattr(user, key, value)
                
                results.append({
                    'achievement_id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'rewards': {
                        'crystals': achievement.reward_crystals,
                        'bonus_stats': achievement.bonus_stats
                    }
                })
        
        return results
