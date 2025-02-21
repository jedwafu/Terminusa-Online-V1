"""
Game Configuration Settings
"""

# Admin Account Settings
ADMIN_USERNAME = "adminbb"
ADMIN_WALLET = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"

# Currency Settings
CRYSTAL_MAX_SUPPLY = 100_000_000
CRYSTAL_INITIAL_AMOUNT = 100  # Given to new players
EXON_MAX_SUPPLY = 100_000_000  # Define max supply for Exons
EXON_INITIAL_AMOUNT = 100  # Given to new players
SOLANA_MAX_SUPPLY = 100_000_000  # Define max supply for Solana
SOLANA_INITIAL_AMOUNT = 100  # Given to new players

# Tax Settings
CRYSTAL_TAX_RATE = 0.13  # 13%
EXON_TAX_RATE = 0.13    # 13%
SOLANA_TAX_RATE = 0.13  # 13% for Solana
GUILD_CRYSTAL_TAX_RATE = 0.02  # Additional 2%
GUILD_EXON_TAX_RATE = 0.02     # Additional 2%

# Player Settings
INITIAL_STATS = {
    'strength': 10,
    'agility': 10,
    'intelligence': 10,
    'vitality': 10,
    'luck': 10,
    'hp': 100,
    'mp': 100
}

INITIAL_INVENTORY_SLOTS = 20
INVENTORY_SLOT_EXPANSION = 10  # Slots added when purchasing expansion

# Level Settings
LEVEL_EXP_MULTIPLIER = 1.5  # Each level requires 1.5x more exp than previous
BASE_LEVEL_EXP = 1000      # Base exp required for level 2

# Job System Settings
BASIC_JOBS = ['Fighter', 'Mage', 'Assassin', 'Archer', 'Healer']
JOB_RANK_LEVEL_REQUIREMENT = 50  # Levels needed for job rank up

# Hunter Class Settings
HUNTER_CLASSES = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
CLASS_UPGRADE_REQUIREMENTS = {
    'E': {'level': 10, 'gates_cleared': 5},
    'D': {'level': 20, 'gates_cleared': 15},
    'C': {'level': 30, 'gates_cleared': 30},
    'B': {'level': 40, 'gates_cleared': 50},
    'A': {'level': 50, 'gates_cleared': 75},
    'S': {'level': 60, 'gates_cleared': 100}
}

# Gate Settings
GATE_RANKS = ['E', 'D', 'C', 'B', 'A', 'S', 'Monarch']
GATE_CRYSTAL_REWARDS = {
    'E': {'min': 10, 'max': 50},
    'D': {'min': 40, 'max': 200},
    'C': {'min': 150, 'max': 750},
    'B': {'min': 500, 'max': 2500},
    'A': {'min': 2000, 'max': 10000},
    'S': {'min': 8000, 'max': 40000},
    'Monarch': {'min': 30000, 'max': 150000}
}

# Party Settings
PARTY_REWARD_MULTIPLIERS = {
    1: 1.0,      # Solo
    2: 0.6,      # 2 players
    3: 0.4,      # 3 players
    4: 0.3,      # 4 players
    5: 0.25      # 5+ players
}

# Item Settings
ITEM_RARITIES = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Immortal']
ITEM_RARITY_DROP_RATES = {
    'Common': 0.50,     # 50%
    'Uncommon': 0.25,   # 25%
    'Rare': 0.15,       # 15%
    'Epic': 0.07,       # 7%
    'Legendary': 0.025, # 2.5%
    'Immortal': 0.005   # 0.5%
}

# Mount and Pet Settings
MOUNT_PET_RARITIES = ['Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal']
MOUNT_PET_GACHA_RATES = {
    'Basic': 0.45,        # 45%
    'Intermediate': 0.30, # 30%
    'Excellent': 0.15,    # 15%
    'Legendary': 0.08,    # 8%
    'Immortal': 0.02      # 2%
}

# Shop Items
SHOP_ITEMS = {
    'inventory_expansion': {
        'name': '10 Slot Inventory Expansion',
        'price_crystals': 1000,
        'description': 'Increases inventory capacity by 10 slots'
    },
    'rename_license': {
        'name': 'Rename License',
        'price_crystals': 500,
        'description': 'Allows you to change your character name'
    },
    'job_reset': {
        'name': 'Job Reset License',
        'price_exons': 10,
        'description': 'Reset your job class and return to level 1'
    },
    'job_license': {
        'name': 'Job Change License',
        'price_exons': 20,
        'description': 'Required for job change quests'
    },
    'hunter_upgrade_license': {
        'name': 'Hunter Class Upgrade License',
        'price_exons': 50,
        'description': 'Required for hunter class upgrade'
    },
    'remote_shop': {
        'name': 'Remote Shop License',
        'price_exons': 30,
        'description': 'Access shop anywhere, including inside gates'
    },
    'basic_resurrection': {
        'name': 'Basic Resurrection Potion',
        'price_exons': 5,
        'description': 'Revive with 50% HP'
    },
    'advanced_resurrection': {
        'name': 'Advanced Resurrection Potion',
        'price_exons': 15,
        'description': 'Revive with 100% HP, works on decapitated status'
    }
}

# Potion Settings
POTIONS = {
    'health_potion': {
        'name': 'Health Potion',
        'heal': 50,
        'price_crystals': 100
    },
    'mana_potion': {
        'name': 'Mana Potion',
        'restore': 50,
        'price_crystals': 100
    },
    'high_health_potion': {
        'name': 'High Health Potion',
        'heal': 200,
        'price_crystals': 300
    },
    'high_mana_potion': {
        'name': 'High Mana Potion',
        'restore': 200,
        'price_crystals': 300
    }
}

# Antidote Settings
ANTIDOTES = {
    'chill_antidote': {
        'name': 'Chill Antidote',
        'cures': ['Burned'],
        'price_crystals': 150
    },
    'cleansing_antidote': {
        'name': 'Cleansing Antidote',
        'cures': ['Poisoned'],
        'price_crystals': 150
    },
    'flame_antidote': {
        'name': 'Flame Antidote',
        'cures': ['Frozen'],
        'price_crystals': 150
    },
    'shilajit_antidote': {
        'name': 'Shilajit Antidote',
        'cures': ['Feared', 'Confused'],
        'price_crystals': 200
    }
}

# Guild Settings
GUILD_CREATION_COST = {
    'exons': 100,
    'crystals': 10000
}

# Referral System
REFERRAL_REWARDS = {
    100: 1000,    # 1,000 crystals for 100 referrals
    200: 2500,    # 2,500 crystals for 200 referrals
    300: 5000,    # 5,000 crystals for 300 referrals
    400: 10000,   # 10,000 crystals for 400 referrals
    500: 20000    # 20,000 crystals for 500 referrals
}
REFERRAL_LEVEL_REQUIREMENT = 50  # Referred players must reach this level

# Gambling System
FLIP_COIN_MIN_BET = 100    # Minimum crystal bet
FLIP_COIN_MAX_BET = 10000  # Maximum crystal bet

# Combat Settings
EQUIPMENT_DURABILITY_LOSS = {
    'damage_taken': 0.01,  # 0.1% per 1% HP lost
    'mana_used': 0.005,    # 0.05% per 1% MP used
    'time_factor': 0.1     # 0.1% per minute in gate
}

# Status Effect Chances
STATUS_EFFECT_CHANCES = {
    'burn': 0.15,
    'poison': 0.15,
    'freeze': 0.15,
    'fear': 0.10,
    'confuse': 0.10,
    'dismember': 0.05,
    'decapitate': 0.02
}

# AI Agent Settings
AI_CONSIDERATION_FACTORS = [
    'activity_history',
    'job_class',
    'hunter_class',
    'level',
    'stats',
    'equipment',
    'achievements',
    'quest_history',
    'combat_style',
    'party_preference',
    'gambling_frequency',
    'market_activity'
]
"""
</edit_file>

Next, I will proceed with updating the `game_handler.py` file to implement the necessary changes for the new currency system and mechanics.
