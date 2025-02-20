#!/usr/bin/env python3
"""Initialize game data with basic configurations and starter content"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import app, db
from models import *

def init_currencies():
    """Initialize basic currencies"""
    print("Initializing currencies...")
    
    currencies = [
        {
            'name': 'Solana',
            'symbol': 'SOL',
            'type': CurrencyType.SOLANA,
            'admin_wallet': 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw',
            'base_tax_rate': 0.13,
            'guild_tax_rate': 0.02,
            'is_active': True,
            'can_earn_in_gates': False
        },
        {
            'name': 'Exon',
            'symbol': 'EXON',
            'type': CurrencyType.EXON,
            'admin_wallet': 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw',
            'base_tax_rate': 0.13,
            'guild_tax_rate': 0.02,
            'is_active': True,
            'can_earn_in_gates': False
        },
        {
            'name': 'Crystal',
            'symbol': 'CRYS',
            'type': CurrencyType.CRYSTAL,
            'admin_username': 'adminbb',
            'max_supply': 100_000_000,
            'current_supply': 0,
            'base_tax_rate': 0.13,
            'guild_tax_rate': 0.02,
            'is_active': True,
            'can_earn_in_gates': True
        }
    ]
    
    for data in currencies:
        currency = Currency(**data)
        db.session.add(currency)
    
    db.session.commit()
    print("Currencies initialized!")

def init_base_items():
    """Initialize basic items"""
    print("Initializing base items...")
    
    items = [
        # Basic Equipment
        {
            'name': 'Wooden Sword',
            'description': 'A basic training sword',
            'item_type': ItemType.WEAPON,
            'grade': ItemGrade.BASIC,
            'slot': ItemSlot.WEAPON,
            'level_requirement': 1,
            'durability_max': 100,
            'crystal_price': 100,
            'stats': {
                'physical_attack': 5,
                'critical_chance': 1.0
            }
        },
        {
            'name': 'Leather Armor',
            'description': 'Basic protective gear',
            'item_type': ItemType.ARMOR,
            'grade': ItemGrade.BASIC,
            'slot': ItemSlot.CHEST,
            'level_requirement': 1,
            'durability_max': 100,
            'crystal_price': 100,
            'stats': {
                'physical_defense': 5,
                'magical_defense': 2
            }
        },
        
        # Consumables
        {
            'name': 'Health Potion',
            'description': 'Restores 100 HP',
            'item_type': ItemType.CONSUMABLE,
            'grade': ItemGrade.BASIC,
            'is_stackable': True,
            'max_stack': 99,
            'crystal_price': 50,
            'effects': {
                'heal': 100,
                'duration': 0
            }
        },
        {
            'name': 'Mana Potion',
            'description': 'Restores 100 MP',
            'item_type': ItemType.CONSUMABLE,
            'grade': ItemGrade.BASIC,
            'is_stackable': True,
            'max_stack': 99,
            'crystal_price': 50,
            'effects': {
                'restore_mp': 100,
                'duration': 0
            }
        },
        
        # Licenses
        {
            'name': 'Job Reset License',
            'description': 'Allows you to reset your job',
            'item_type': ItemType.LICENSE,
            'grade': ItemGrade.BASIC,
            'is_stackable': False,
            'exon_price': 100,
            'effects': {
                'reset_job': True
            }
        },
        {
            'name': 'Remote Shop License',
            'description': 'Access shop anywhere',
            'item_type': ItemType.LICENSE,
            'grade': ItemGrade.BASIC,
            'is_stackable': False,
            'exon_price': 200,
            'effects': {
                'remote_shop': True
            }
        }
    ]
    
    for data in items:
        item = Item(**data)
        db.session.add(item)
    
    db.session.commit()
    print("Base items initialized!")

def init_base_skills():
    """Initialize basic skills for each job"""
    print("Initializing base skills...")
    
    skills = [
        # Fighter Skills
        {
            'name': 'Slash',
            'description': 'Basic sword attack',
            'required_job': 'Fighter',
            'required_level': 1,
            'mana_cost': 0,
            'cooldown': 0,
            'damage_type': 'physical',
            'base_power': 10,
            'scaling_stat': 'strength',
            'scaling_factor': 1.0
        },
        {
            'name': 'Power Strike',
            'description': 'Powerful single target attack',
            'required_job': 'Fighter',
            'required_level': 5,
            'mana_cost': 20,
            'cooldown': 10,
            'damage_type': 'physical',
            'base_power': 30,
            'scaling_stat': 'strength',
            'scaling_factor': 1.5
        },
        
        # Mage Skills
        {
            'name': 'Fire Bolt',
            'description': 'Basic fire magic',
            'required_job': 'Mage',
            'required_level': 1,
            'mana_cost': 10,
            'cooldown': 2,
            'damage_type': 'magical',
            'base_power': 15,
            'scaling_stat': 'intelligence',
            'scaling_factor': 1.2,
            'status_effect': 'burned',
            'effect_chance': 0.2,
            'effect_duration': 5
        },
        
        # Healer Skills
        {
            'name': 'Heal',
            'description': 'Basic healing spell',
            'required_job': 'Healer',
            'required_level': 1,
            'mana_cost': 20,
            'cooldown': 5,
            'damage_type': 'heal',
            'base_power': 50,
            'scaling_stat': 'wisdom',
            'scaling_factor': 1.5
        },
        {
            'name': 'Cure',
            'description': 'Removes status effects',
            'required_job': 'Healer',
            'required_level': 10,
            'mana_cost': 30,
            'cooldown': 15,
            'damage_type': 'heal',
            'base_power': 0,
            'scaling_stat': 'wisdom',
            'scaling_factor': 0
        }
    ]
    
    for data in skills:
        skill = Skill(**data)
        db.session.add(skill)
    
    db.session.commit()
    print("Base skills initialized!")

def init_starter_gates():
    """Initialize starter gates"""
    print("Initializing starter gates...")
    
    gates = [
        {
            'name': 'Training Ground',
            'description': 'A basic gate for beginners',
            'grade': GateGrade.F,
            'level_requirement': 1,
            'rank_requirement': GateGrade.F,
            'min_players': 1,
            'max_players': 4,
            'base_crystal_reward': 10,
            'base_exp_reward': 100,
            'loot_table': {
                'common': {'chance': 0.7, 'items': ['Wooden Sword', 'Leather Armor']},
                'rare': {'chance': 0.3, 'items': ['Health Potion', 'Mana Potion']}
            },
            'monster_level_bonus': 1.0,
            'monster_stat_bonus': 1.0,
            'monster_count_bonus': 1.0,
            'time_limit': 1800  # 30 minutes
        }
    ]
    
    for data in gates:
        gate = Gate(**data)
        db.session.add(gate)
    
    db.session.commit()
    print("Starter gates initialized!")

def init_ai_models():
    """Initialize AI models"""
    print("Initializing AI models...")
    
    models = [
        {
            'name': 'Quest Generator',
            'model_type': AIModelType.QUEST,
            'description': 'Generates personalized quests based on player activity',
            'version': '1.0.0',
            'parameters': {
                'learning_rate': 0.01,
                'batch_size': 32,
                'epochs': 100
            },
            'features': [
                'player_level',
                'player_class',
                'activity_history',
                'completion_rate',
                'play_style'
            ],
            'weights': {},  # Initial weights would be set by training
            'activity_weights': {
                'gate_hunting': 1.0,
                'gambling': 0.5,
                'trading': 0.7,
                'questing': 1.0
            },
            'player_type_weights': {
                'aggressive': 1.2,
                'casual': 0.8,
                'social': 1.0
            }
        },
        {
            'name': 'Gacha System',
            'model_type': AIModelType.GACHA,
            'description': 'Controls gacha probabilities based on player behavior',
            'version': '1.0.0',
            'parameters': {
                'base_legendary_rate': 0.01,
                'pity_increment': 0.001,
                'activity_bonus_cap': 0.05
            },
            'features': [
                'total_pulls',
                'spending_pattern',
                'activity_level',
                'account_age'
            ],
            'weights': {},
            'fairness_parameters': {
                'min_legendary_per_month': 1,
                'max_spend_limit': 1000
            }
        }
    ]
    
    for data in models:
        model = AIModel(**data)
        db.session.add(model)
    
    db.session.commit()
    print("AI models initialized!")

def main():
    """Main initialization function"""
    with app.app_context():
        print("Starting game data initialization...")
        
        try:
            init_currencies()
            init_base_items()
            init_base_skills()
            init_starter_gates()
            init_ai_models()
            
            print("\nGame data initialization complete!")
            
        except Exception as e:
            print(f"Error during initialization: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    main()
