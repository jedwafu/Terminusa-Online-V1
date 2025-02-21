from typing import Dict, List, Optional
from decimal import Decimal
import random
from datetime import datetime
from models import db, User, Mount, Pet, Transaction
from game_config import (
    MOUNT_PET_RARITIES,
    MOUNT_PET_GACHA_RATES,
    ADMIN_USERNAME
)
from ai_agent import AIAgent

class GachaSystem:
    def __init__(self):
        self._admin_user = None
        self.ai_agent = AIAgent()

    @property
    def admin_user(self):
        """Lazy load admin user when needed"""
        if self._admin_user is None:
            from flask import current_app
            with current_app.app_context():
                self._admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
        return self._admin_user

    def roll_mount(self, user: User, amount: int = 1) -> Dict:
        """Roll for mounts using Exons"""
        MOUNT_COST = Decimal("10")  # 10 Exons per roll
        total_cost = MOUNT_COST * amount

        if user.exons_balance < total_cost:
            return {
                "success": False,
                "message": "Insufficient Exons balance"
            }

        try:
            # Get player profile for AI-adjusted rates
            profile = self.ai_agent.analyze_player(user)
            adjusted_rates = self.ai_agent.calculate_gacha_odds(user, "mount")

            results = []
            for _ in range(amount):
                rarity = self._determine_rarity(adjusted_rates)
                mount = self._generate_mount(rarity, user.level)
                results.append({
                    'mount_id': mount.id,
                    'name': mount.name,
                    'rarity': mount.rarity,
                    'stats': mount.stats
                })

            # Process payment
            user.exons_balance -= total_cost

            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type="mount_gacha",
                currency="exons",
                amount=total_cost,
                tax_amount=Decimal("0")  # No tax on gacha
            )
            db.session.add(transaction)
            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully rolled {amount} mount(s)",
                "results": results,
                "cost": str(total_cost)
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to process mount roll: {str(e)}"
            }

    def roll_pet(self, user: User, amount: int = 1) -> Dict:
        """Roll for pets using Exons"""
        PET_COST = Decimal("8")  # 8 Exons per roll
        total_cost = PET_COST * amount

        if user.exons_balance < total_cost:
            return {
                "success": False,
                "message": "Insufficient Exons balance"
            }

        try:
            # Get player profile for AI-adjusted rates
            profile = self.ai_agent.analyze_player(user)
            adjusted_rates = self.ai_agent.calculate_gacha_odds(user, "pet")

            results = []
            for _ in range(amount):
                rarity = self._determine_rarity(adjusted_rates)
                pet = self._generate_pet(rarity, user.level)
                results.append({
                    'pet_id': pet.id,
                    'name': pet.name,
                    'rarity': pet.rarity,
                    'abilities': pet.abilities
                })

            # Process payment
            user.exons_balance -= total_cost

            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type="pet_gacha",
                currency="exons",
                amount=total_cost,
                tax_amount=Decimal("0")  # No tax on gacha
            )
            db.session.add(transaction)
            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully rolled {amount} pet(s)",
                "results": results,
                "cost": str(total_cost)
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to process pet roll: {str(e)}"
            }

    def _determine_rarity(self, adjusted_rates: Dict[str, float]) -> str:
        """Determine rarity based on adjusted rates"""
        roll = random.random()
        cumulative = 0
        for rarity, rate in adjusted_rates.items():
            cumulative += rate
            if roll <= cumulative:
                return rarity
        return "Basic"  # Fallback to basic if something goes wrong

    def _generate_mount(self, rarity: str, level: int) -> Mount:
        """Generate a mount with the given rarity"""
        # Base stats based on rarity
        rarity_multiplier = {
            'Basic': 1,
            'Intermediate': 1.5,
            'Excellent': 2,
            'Legendary': 3,
            'Immortal': 5
        }[rarity]

        # Generate mount name
        mount_types = ['Horse', 'Dragon', 'Griffin', 'Phoenix', 'Wyvern']
        mount_prefixes = {
            'Basic': ['Sturdy', 'Reliable', 'Common'],
            'Intermediate': ['Swift', 'Strong', 'Agile'],
            'Excellent': ['Majestic', 'Powerful', 'Noble'],
            'Legendary': ['Ancient', 'Mythical', 'Divine'],
            'Immortal': ['Eternal', 'Celestial', 'Godly']
        }

        name = f"{random.choice(mount_prefixes[rarity])} {random.choice(mount_types)}"

        # Calculate stats
        base_stats = {
            'speed': 10,
            'stamina': 100,
            'carrying_capacity': 50
        }
        stats = {k: int(v * rarity_multiplier * (level/10)) for k, v in base_stats.items()}

        mount = Mount(
            name=name,
            rarity=rarity,
            level_requirement=max(1, level - 10),
            stats=stats,
            is_tradeable=(rarity != 'Immortal')  # Immortal mounts cannot be traded
        )
        db.session.add(mount)
        return mount

    def _generate_pet(self, rarity: str, level: int) -> Pet:
        """Generate a pet with the given rarity"""
        # Base abilities based on rarity
        rarity_abilities = {
            'Basic': ['Item Finder'],
            'Intermediate': ['Item Finder', 'Combat Support'],
            'Excellent': ['Item Finder', 'Combat Support', 'Stat Boost'],
            'Legendary': ['Item Finder', 'Combat Support', 'Stat Boost', 'Special Skill'],
            'Immortal': ['Item Finder', 'Combat Support', 'Stat Boost', 'Special Skill', 'Unique Ability']
        }

        # Generate pet name
        pet_types = ['Fox', 'Wolf', 'Cat', 'Bird', 'Dragon']
        pet_prefixes = {
            'Basic': ['Little', 'Young', 'Small'],
            'Intermediate': ['Clever', 'Quick', 'Sharp'],
            'Excellent': ['Wise', 'Mighty', 'Grand'],
            'Legendary': ['Ancient', 'Mystic', 'Divine'],
            'Immortal': ['Eternal', 'Celestial', 'Godly']
        }

        name = f"{random.choice(pet_prefixes[rarity])} {random.choice(pet_types)}"

        # Generate abilities
        abilities = rarity_abilities[rarity]
        if rarity == 'Immortal':
            unique_abilities = [
                'Time Manipulation',
                'Reality Bending',
                'Soul Link',
                'Dimensional Travel',
                'Fate Weaving'
            ]
            abilities[-1] = random.choice(unique_abilities)

        pet = Pet(
            name=name,
            rarity=rarity,
            level_requirement=max(1, level - 10),
            abilities=abilities,
            is_tradeable=(rarity != 'Immortal')  # Immortal pets cannot be traded
        )
        db.session.add(pet)
        return pet

    def get_rates(self, user: User, gacha_type: str) -> Dict[str, float]:
        """Get current gacha rates for the user"""
        profile = self.ai_agent.analyze_player(user)
        return self.ai_agent.calculate_gacha_odds(user, gacha_type)

    def get_pity_info(self, user: User) -> Dict:
        """Get pity system information for the user"""
        # Pity system guarantees a higher rarity after X unsuccessful rolls
        PITY_THRESHOLDS = {
            'Legendary': 50,  # Guaranteed Legendary within 50 rolls
            'Immortal': 100   # Guaranteed Immortal within 100 rolls
        }

        # Get user's roll history
        mount_rolls = Transaction.query.filter_by(
            user_id=user.id,
            type="mount_gacha"
        ).count()
        pet_rolls = Transaction.query.filter_by(
            user_id=user.id,
            type="pet_gacha"
        ).count()

        return {
            'mount_pity': {
                'rolls_until_legendary': max(0, PITY_THRESHOLDS['Legendary'] - (mount_rolls % PITY_THRESHOLDS['Legendary'])),
                'rolls_until_immortal': max(0, PITY_THRESHOLDS['Immortal'] - (mount_rolls % PITY_THRESHOLDS['Immortal']))
            },
            'pet_pity': {
                'rolls_until_legendary': max(0, PITY_THRESHOLDS['Legendary'] - (pet_rolls % PITY_THRESHOLDS['Legendary'])),
                'rolls_until_immortal': max(0, PITY_THRESHOLDS['Immortal'] - (pet_rolls % PITY_THRESHOLDS['Immortal']))
            }
        }
