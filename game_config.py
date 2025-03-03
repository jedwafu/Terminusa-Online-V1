"""
Game configuration settings for Terminusa Online
"""
from decimal import Decimal

# Currency Configuration
MAX_CRYSTAL_SUPPLY = 100_000_000
CRYSTAL_TAX_RATE = Decimal('0.13')  # 13%
EXON_TAX_RATE = Decimal('0.13')     # 13%
GUILD_CRYSTAL_TAX_RATE = Decimal('0.02')  # Additional 2%
GUILD_EXON_TAX_RATE = Decimal('0.02')     # Additional 2%

# Admin Configuration
ADMIN_USERNAME = "adminbb"
ADMIN_WALLET = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"

# Inventory Configuration
INVENTORY_INITIAL_SIZE = 20
INVENTORY_EXPANSION_SIZE = 10
INVENTORY_EXPANSION_COST = 100  # Crystals

# License Costs
RENAME_LICENSE_COST = 100        # Crystals
JOB_RESET_COST = 100            # Exons
JOB_LICENSE_COST = 200          # Exons
HUNTER_CLASS_UPGRADE_COST = 500  # Exons
REMOTE_SHOP_LICENSE_COST = 300   # Exons

# Resurrection Costs
BASIC_RESURRECTION_COST = 100     # Exons
HIGHER_RESURRECTION_COST = 300    # Exons

# Job System Configuration
JOB_CLASSES = {
    'Fighter': {
        'base_hp': 120,
        'base_mp': 50,
        'base_attack': 10,
        'base_defense': 8,
        'hp_per_level': 12,
        'mp_per_level': 5
    },
    'Mage': {
        'base_hp': 80,
        'base_mp': 100,
        'base_attack': 5,
        'base_defense': 4,
        'hp_per_level': 8,
        'mp_per_level': 10
    },
    'Assassin': {
        'base_hp': 90,
        'base_mp': 60,
        'base_attack': 12,
        'base_defense': 5,
        'hp_per_level': 9,
        'mp_per_level': 6
    },
    'Archer': {
        'base_hp': 85,
        'base_mp': 70,
        'base_attack': 11,
        'base_defense': 4,
        'hp_per_level': 8.5,
        'mp_per_level': 7
    },
    'Healer': {
        'base_hp': 95,
        'base_mp': 90,
        'base_attack': 4,
        'base_defense': 6,
        'hp_per_level': 9.5,
        'mp_per_level': 9
    }
}

# Hunter Classes
HUNTER_CLASSES = ['F', 'E', 'D', 'C', 'B', 'A', 'S']

# Element System
ELEMENTS = {
    'neutral': {
        'strengths': [],
        'weaknesses': []
    },
    'holy': {
        'strengths': ['shadow'],
        'weaknesses': []
    },
    'fire': {
        'strengths': ['earth'],
        'weaknesses': ['water']
    },
    'water': {
        'strengths': ['fire'],
        'weaknesses': ['lightning']
    },
    'lightning': {
        'strengths': ['water'],
        'weaknesses': ['earth']
    },
    'earth': {
        'strengths': ['lightning'],
        'weaknesses': ['fire']
    },
    'shadow': {
        'strengths': [],
        'weaknesses': ['holy']
    }
}

# Element Damage Modifiers
ELEMENT_DAMAGE_BONUS = Decimal('0.5')    # 50% more damage
ELEMENT_DAMAGE_PENALTY = Decimal('0.25')  # 25% less damage

# Status Effects
STATUS_EFFECTS = {
    'burn': {
        'duration': 5,  # turns
        'damage_per_turn': 5,
        'cure': 'Chill Antidote'
    },
    'poisoned': {
        'duration': 8,
        'damage_per_turn': 3,
        'cure': 'Cleansing Antidote'
    },
    'frozen': {
        'duration': 3,
        'damage_per_turn': 0,
        'movement_penalty': True,
        'cure': 'Flame Antidote'
    },
    'feared': {
        'duration': 4,
        'accuracy_penalty': 0.5,  # 50% accuracy reduction
        'cure': 'Shilajit Antidote'
    },
    'confused': {
        'duration': 3,
        'friendly_fire_chance': 0.3,  # 30% chance to hit allies
        'cure': 'Shilajit Antidote'
    },
    'dismembered': {
        'duration': -1,  # permanent until cured
        'damage_penalty': 0.5,  # 50% damage reduction
        'cure': 'Regenerate Skill'
    },
    'decapitated': {
        'duration': -1,  # permanent until cured
        'instant_death': True,
        'cure': 'Higher Resurrection Potion'
    },
    'shadow': {
        'duration': -1,  # permanent until cured
        'no_actions': True,
        'cure': 'Higher Resurrection Potion'
    }
}

# Gate System
GATE_GRADES = {
    'F': {
        'min_level': 1,
        'max_level': 10,
        'crystal_reward_range': (10, 50),
        'equipment_drop_rate': 0.1  # 10%
    },
    'E': {
        'min_level': 10,
        'max_level': 25,
        'crystal_reward_range': (40, 100),
        'equipment_drop_rate': 0.15
    },
    'D': {
        'min_level': 25,
        'max_level': 50,
        'crystal_reward_range': (90, 200),
        'equipment_drop_rate': 0.2
    },
    'C': {
        'min_level': 50,
        'max_level': 100,
        'crystal_reward_range': (180, 400),
        'equipment_drop_rate': 0.25
    },
    'B': {
        'min_level': 100,
        'max_level': 200,
        'crystal_reward_range': (350, 800),
        'equipment_drop_rate': 0.3
    },
    'A': {
        'min_level': 200,
        'max_level': 400,
        'crystal_reward_range': (700, 1500),
        'equipment_drop_rate': 0.35
    },
    'S': {
        'min_level': 400,
        'max_level': 999,
        'crystal_reward_range': (1400, 3000),
        'equipment_drop_rate': 0.4
    }
}

# Party System
PARTY_CONFIG = {
    'max_members': 10,
    'reward_scaling': {
        1: 1.0,      # Solo player gets 100%
        2: 0.9,      # 2 players get 90% each
        3: 0.85,     # 3 players get 85% each
        4: 0.8,      # etc.
        5: 0.75,
        6: 0.7,
        7: 0.65,
        8: 0.6,
        9: 0.55,
        10: 0.5
    }
}

# Equipment System
EQUIPMENT_GRADES = {
    'Basic': {
        'upgrade_success_rate': 0.9,     # 90%
        'upgrade_cost_multiplier': 1.0
    },
    'Intermediate': {
        'upgrade_success_rate': 0.7,
        'upgrade_cost_multiplier': 1.5
    },
    'Excellent': {
        'upgrade_success_rate': 0.5,
        'upgrade_cost_multiplier': 2.0
    },
    'Legendary': {
        'upgrade_success_rate': 0.3,
        'upgrade_cost_multiplier': 3.0
    },
    'Immortal': {
        'upgrade_success_rate': 0.1,
        'upgrade_cost_multiplier': 5.0
    }
}

# Equipment Durability
DURABILITY_CONFIG = {
    'max_durability': 100,
    'damage_loss_rate': 0.1,     # 0.1 durability lost per 1% HP lost
    'mana_loss_rate': 0.05,      # 0.05 durability lost per 1% MP used
    'time_loss_rate': 0.1,       # 0.1 durability lost per minute in gate
    'repair_cost_rate': 1        # 1 Crystal per 1 durability point
}

# Guild System
GUILD_CONFIG = {
    'creation_cost': {
        'crystals': 10000,
        'exons': 100
    },
    'max_members': 100,
    'quest_reward_multiplier': 1.2,  # 20% bonus rewards
    'quest_tax_rate': Decimal('0.15')  # 15% tax on guild quest rewards
}

# Referral System
REFERRAL_REWARDS = {
    100: 1000,    # 1000 Crystals for 100 referrals
    200: 2500,    # 2500 Crystals for 200 referrals
    300: 5000,    # etc.
    400: 10000,
    500: 20000
}

# Loyalty System
LOYALTY_REWARDS = {
    'exons': {
        1000: Decimal('0.01'),    # 1% monthly reward for holding 1000 EXON
        5000: Decimal('0.015'),   # 1.5% for 5000 EXON
        10000: Decimal('0.02'),   # etc.
        50000: Decimal('0.025'),
        100000: Decimal('0.03')
    },
    'crystals': {
        10000: Decimal('0.02'),   # 2% monthly reward for holding 10000 Crystals
        50000: Decimal('0.025'),  # etc.
        100000: Decimal('0.03'),
        500000: Decimal('0.035'),
        1000000: Decimal('0.04')
    }
}

# Gambling System
GAMBLING_CONFIG = {
    'min_bet': 100,              # Minimum bet in Crystals
    'max_bet': 10000,            # Maximum bet in Crystals
    'base_win_chance': 0.48,     # Base 48% chance to win
    'max_daily_bets': 100,       # Maximum bets per day
    'win_multiplier': Decimal('2.0')  # Double your bet on win
}
