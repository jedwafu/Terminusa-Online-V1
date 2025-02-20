#!/usr/bin/env python3
"""Combat and gate management script for Terminusa Online"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import app, db
from models import (
    Gate, GateGrade, MagicBeast, MagicBeastType,
    GateSession, AIBehavior, gate_magic_beasts,
    PlayerCharacter, HealthStatus
)

def check_gates(args):
    """Check gate status and activity"""
    with app.app_context():
        print("Gate Status Report")
        print("=" * 50)
        
        gates = Gate.query.all()
        print(f"\nTotal Gates: {len(gates)}")
        
        for grade in GateGrade:
            count = Gate.query.filter_by(grade=grade).count()
            print(f"{grade.value:8} Gates: {count}")
        
        print("\nDetailed Gate Analysis:")
        for gate in gates:
            print(f"\n{gate.name} ({gate.grade.value})")
            print("-" * 30)
            print(f"Level Req: {gate.level_requirement}")
            print(f"Rank Req: {gate.rank_requirement.value}")
            print(f"Players: {gate.min_players}-{gate.max_players}")
            
            # Get active sessions
            active_sessions = gate.sessions.filter_by(status='active').count()
            print(f"Active Sessions: {active_sessions}")
            
            # Success rate (last 100 sessions)
            recent_sessions = gate.sessions\
                .filter(GateSession.status.in_(['completed', 'failed']))\
                .order_by(GateSession.completed_at.desc())\
                .limit(100).all()
            
            if recent_sessions:
                success_rate = len([s for s in recent_sessions if s.status == 'completed']) / len(recent_sessions)
                print(f"Success Rate: {success_rate:.1%}")
                
                avg_time = sum(s.time_taken for s in recent_sessions if s.time_taken) / len(recent_sessions)
                print(f"Avg Clear Time: {avg_time:.0f} seconds")
            
            # Magic Beast distribution
            print("\nMagic Beasts:")
            for assoc in gate.magic_beasts:
                beast = assoc.magic_beast
                print(f"- {beast.name} ({beast.beast_type.value})")
                print(f"  Spawn: {assoc.spawn_rate:.1%} ({assoc.min_count}-{assoc.max_count})")

def analyze_combat(args):
    """Analyze combat statistics"""
    with app.app_context():
        print("Combat Analysis Report")
        print("=" * 50)
        
        # Time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=args.days)
        
        print(f"\nAnalyzing period: {start_date.date()} to {end_date.date()}")
        
        # Get completed sessions
        sessions = GateSession.query\
            .filter(GateSession.completed_at >= start_date)\
            .filter(GateSession.status.in_(['completed', 'failed']))\
            .all()
        
        print(f"\nTotal Sessions: {len(sessions)}")
        
        # Analyze by grade
        grade_stats = {}
        for session in sessions:
            grade = session.gate.grade.value
            if grade not in grade_stats:
                grade_stats[grade] = {'total': 0, 'completed': 0, 'failed': 0}
            
            grade_stats[grade]['total'] += 1
            if session.status == 'completed':
                grade_stats[grade]['completed'] += 1
            else:
                grade_stats[grade]['failed'] += 1
        
        print("\nSuccess Rates by Grade:")
        for grade, stats in sorted(grade_stats.items()):
            success_rate = stats['completed'] / stats['total']
            print(f"{grade:8}: {success_rate:.1%} ({stats['completed']}/{stats['total']})")
        
        # Analyze party size impact
        size_stats = {}
        for session in sessions:
            size = len(session.damage_dealt) if session.damage_dealt else 1
            if size not in size_stats:
                size_stats[size] = {'total': 0, 'completed': 0}
            
            size_stats[size]['total'] += 1
            if session.status == 'completed':
                size_stats[size]['completed'] += 1
        
        print("\nSuccess Rates by Party Size:")
        for size, stats in sorted(size_stats.items()):
            success_rate = stats['completed'] / stats['total']
            print(f"{size:2} players: {success_rate:.1%} ({stats['completed']}/{stats['total']})")
        
        # Analyze deaths
        total_deaths = sum(len(session.player_deaths) for session in sessions if session.player_deaths)
        avg_deaths = total_deaths / len(sessions) if sessions else 0
        print(f"\nAverage Deaths per Session: {avg_deaths:.1f}")

def manage_beasts(args):
    """Manage magic beasts"""
    with app.app_context():
        print("Magic Beast Management")
        print("=" * 50)
        
        beasts = MagicBeast.query.all()
        print(f"\nTotal Beasts: {len(beasts)}")
        
        for beast in beasts:
            print(f"\n{beast.name}")
            print("-" * 30)
            print(f"Type: {beast.beast_type.value}")
            print(f"Level: {beast.level}")
            
            # Stats
            print("\nStats:")
            print(f"HP: {beast.hp}")
            print(f"MP: {beast.mp}")
            print(f"Physical Attack: {beast.physical_attack}")
            print(f"Magical Attack: {beast.magical_attack}")
            print(f"Physical Defense: {beast.physical_defense}")
            print(f"Magical Defense: {beast.magical_defense}")
            print(f"Speed: {beast.speed}")
            
            # AI Behavior
            behavior = beast.ai_behavior
            print(f"\nAI Behavior: {behavior.name}")
            print(f"Type: {behavior.behavior_type}")
            
            if not args.view_only:
                # Balance stats based on success rates
                gates = Gate.query.join(gate_magic_beasts)\
                    .filter(gate_magic_beasts.c.magic_beast_id == beast.id)\
                    .all()
                
                total_success = 0
                total_sessions = 0
                
                for gate in gates:
                    recent_sessions = gate.sessions\
                        .filter(GateSession.status.in_(['completed', 'failed']))\
                        .order_by(GateSession.completed_at.desc())\
                        .limit(100).all()
                    
                    if recent_sessions:
                        successes = len([s for s in recent_sessions if s.status == 'completed'])
                        total_success += successes
                        total_sessions += len(recent_sessions)
                
                if total_sessions > 0:
                    success_rate = total_success / total_sessions
                    
                    # Adjust stats if success rate is too high/low
                    if success_rate > 0.7:  # Too easy
                        adjustment = 1.1  # Increase stats by 10%
                        print("\nIncreasing difficulty...")
                    elif success_rate < 0.3:  # Too hard
                        adjustment = 0.9  # Decrease stats by 10%
                        print("\nDecreasing difficulty...")
                    else:
                        adjustment = 1.0
                    
                    if adjustment != 1.0:
                        beast.hp = int(beast.hp * adjustment)
                        beast.physical_attack = int(beast.physical_attack * adjustment)
                        beast.magical_attack = int(beast.magical_attack * adjustment)
                        beast.physical_defense = int(beast.physical_defense * adjustment)
                        beast.magical_defense = int(beast.magical_defense * adjustment)
                        
                        print(f"New HP: {beast.hp}")
                        print(f"New Physical Attack: {beast.physical_attack}")
                        print(f"New Magical Attack: {beast.magical_attack}")
                        print(f"New Physical Defense: {beast.physical_defense}")
                        print(f"New Magical Defense: {beast.magical_defense}")
        
        if not args.view_only:
            db.session.commit()
            print("\nMagic beasts updated!")

def export_combat_data(args):
    """Export combat system data"""
    with app.app_context():
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'gates': [],
            'magic_beasts': [],
            'recent_sessions': []
        }
        
        # Get gate data
        gates = Gate.query.all()
        for gate in gates:
            gate_data = {
                'name': gate.name,
                'grade': gate.grade.value,
                'level_requirement': gate.level_requirement,
                'rank_requirement': gate.rank_requirement.value,
                'players': {
                    'min': gate.min_players,
                    'max': gate.max_players
                },
                'rewards': {
                    'crystal': gate.base_crystal_reward,
                    'exp': gate.base_exp_reward
                },
                'difficulty': {
                    'monster_level': gate.monster_level_bonus,
                    'monster_stat': gate.monster_stat_bonus,
                    'monster_count': gate.monster_count_bonus
                },
                'magic_beasts': [
                    {
                        'id': assoc.magic_beast_id,
                        'spawn_rate': assoc.spawn_rate,
                        'min_count': assoc.min_count,
                        'max_count': assoc.max_count
                    }
                    for assoc in gate.magic_beasts
                ]
            }
            data['gates'].append(gate_data)
        
        # Get magic beast data
        beasts = MagicBeast.query.all()
        for beast in beasts:
            beast_data = {
                'name': beast.name,
                'type': beast.beast_type.value,
                'level': beast.level,
                'stats': {
                    'hp': beast.hp,
                    'mp': beast.mp,
                    'physical_attack': beast.physical_attack,
                    'magical_attack': beast.magical_attack,
                    'physical_defense': beast.physical_defense,
                    'magical_defense': beast.magical_defense,
                    'speed': beast.speed
                },
                'ai_behavior': {
                    'name': beast.ai_behavior.name,
                    'type': beast.ai_behavior.behavior_type,
                    'skill_priorities': beast.ai_behavior.skill_priorities,
                    'target_selection': beast.ai_behavior.target_selection
                }
            }
            data['magic_beasts'].append(beast_data)
        
        # Get recent session data
        sessions = GateSession.query\
            .filter(GateSession.completed_at >= datetime.utcnow() - timedelta(days=7))\
            .all()
        
        for session in sessions:
            session_data = {
                'id': session.id,
                'gate_id': session.gate_id,
                'status': session.status,
                'time_taken': session.time_taken,
                'rewards': {
                    'crystal': session.total_crystal_reward,
                    'exp': session.total_exp_reward
                },
                'combat_stats': {
                    'damage_dealt': session.damage_dealt,
                    'damage_taken': session.damage_taken,
                    'healing_done': session.healing_done,
                    'kills': session.kills
                }
            }
            data['recent_sessions'].append(session_data)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_dir = project_root / 'data' / 'combat'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        data_file = data_dir / f'combat_data_{timestamp}.json'
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Combat data exported to: {data_file}")

def main():
    parser = argparse.ArgumentParser(description="Terminusa Online Combat Management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Gates command
    gates_parser = subparsers.add_parser('gates',
                                       help='Check gate status')
    
    # Combat command
    combat_parser = subparsers.add_parser('combat',
                                        help='Analyze combat stats')
    combat_parser.add_argument('--days', type=int, default=7,
                             help='Days of history to analyze')
    
    # Beasts command
    beasts_parser = subparsers.add_parser('beasts',
                                        help='Manage magic beasts')
    beasts_parser.add_argument('--view-only', action='store_true',
                             help='Only view beasts')
    
    # Export command
    export_parser = subparsers.add_parser('export',
                                        help='Export combat data')
    
    args = parser.parse_args()
    
    if args.command == 'gates':
        check_gates(args)
    elif args.command == 'combat':
        analyze_combat(args)
    elif args.command == 'beasts':
        manage_beasts(args)
    elif args.command == 'export':
        export_combat_data(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
