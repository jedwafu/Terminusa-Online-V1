#!/usr/bin/env python3
"""Social systems management script for Terminusa Online"""

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
    Guild, GuildRank, GuildMember, GuildQuest, GuildLog,
    Party, PartyMember, PartyInvitation, PartyLog
)

def check_guilds(args):
    """Check guild status and activity"""
    with app.app_context():
        print("Guild Status Report")
        print("=" * 50)
        
        guilds = Guild.query.all()
        print(f"\nTotal Guilds: {len(guilds)}")
        
        for guild in guilds:
            print(f"\n{guild.name}")
            print("-" * 30)
            print(f"Level: {guild.level}")
            print(f"Experience: {guild.experience:,}")
            print(f"Members: {guild.members.count()}/{guild.max_members}")
            print(f"Crystal Balance: {guild.crystal_balance:,}")
            print(f"Exon Balance: {guild.exon_balance:,}")
            
            # Member breakdown
            members_by_rank = {}
            for member in guild.members:
                members_by_rank[member.rank.value] = members_by_rank.get(member.rank.value, 0) + 1
            
            print("\nMember Ranks:")
            for rank, count in sorted(members_by_rank.items()):
                print(f"{rank:8}: {count:,}")
            
            # Activity stats
            print("\nActivity Stats:")
            print(f"Gates Cleared: {guild.total_gates_cleared:,}")
            print(f"Quests Completed: {guild.total_quests_completed:,}")
            print(f"Boss Kills: {guild.total_boss_kills:,}")
            print(f"Weekly Activity: {guild.weekly_activity:,}")
            
            # Active quests
            active_quests = guild.quests.filter_by(status='active').count()
            print(f"\nActive Quests: {active_quests}")

def analyze_parties(args):
    """Analyze party activity"""
    with app.app_context():
        print("Party Activity Report")
        print("=" * 50)
        
        # Time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=args.days)
        
        print(f"\nAnalyzing period: {start_date.date()} to {end_date.date()}")
        
        # Get active parties
        active_parties = Party.query\
            .filter_by(status='active')\
            .filter(Party.created_at >= start_date)\
            .all()
        
        print(f"\nActive Parties: {len(active_parties)}")
        
        # Size distribution
        size_dist = {}
        for party in active_parties:
            size = party.members.count()
            size_dist[size] = size_dist.get(size, 0) + 1
        
        print("\nParty Size Distribution:")
        for size, count in sorted(size_dist.items()):
            print(f"{size} members: {count:,} parties")
        
        # Gate activity
        parties_in_gates = sum(1 for p in active_parties if p.current_gate_id)
        print(f"\nParties in Gates: {parties_in_gates}")
        
        # Average stats
        avg_level = sum(p.average_level for p in active_parties) / len(active_parties) if active_parties else 0
        avg_luck = sum(p.total_luck for p in active_parties) / len(active_parties) if active_parties else 0
        
        print(f"\nAverages:")
        print(f"Level: {avg_level:.1f}")
        print(f"Luck: {avg_luck:.1f}")

def manage_quests(args):
    """Manage guild quests"""
    with app.app_context():
        print("Guild Quest Management")
        print("=" * 50)
        
        if args.guild:
            guilds = [Guild.query.filter_by(name=args.guild).first()]
            if not guilds[0]:
                print(f"Guild not found: {args.guild}")
                sys.exit(1)
        else:
            guilds = Guild.query.all()
        
        for guild in guilds:
            print(f"\n{guild.name}")
            print("-" * 30)
            
            # Active quests
            active_quests = guild.quests.filter_by(status='active').all()
            print(f"\nActive Quests: {len(active_quests)}")
            
            for quest in active_quests:
                print(f"\n{quest.name}")
                print(f"Started: {quest.start_time}")
                if quest.end_time:
                    print(f"Ends: {quest.end_time}")
                
                # Check progress
                for req, target in quest.requirements.items():
                    current = quest.current_progress.get(req, 0)
                    print(f"{req}: {current}/{target}")
                
                # Check participation
                participants = len(quest.participating_members)
                print(f"Participants: {participants}")
                
                # Auto-complete if requirements met
                if not args.view_only:
                    all_complete = all(
                        quest.current_progress.get(req, 0) >= target
                        for req, target in quest.requirements.items()
                    )
                    
                    if all_complete:
                        quest.status = 'completed'
                        quest.completed_at = datetime.utcnow()
                        
                        # Update guild stats
                        guild.total_quests_completed += 1
                        guild.experience += sum(quest.rewards.values())
                        
                        # Log completion
                        log = GuildLog(
                            guild_id=guild.id,
                            action='quest_complete',
                            details={
                                'quest_id': quest.id,
                                'name': quest.name,
                                'rewards': quest.rewards
                            }
                        )
                        db.session.add(log)
                        
                        print("Quest completed automatically!")
            
            if not args.view_only:
                db.session.commit()

def export_social_data(args):
    """Export social system data"""
    with app.app_context():
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'guilds': [],
            'parties': []
        }
        
        # Get guild data
        guilds = Guild.query.all()
        for guild in guilds:
            guild_data = {
                'name': guild.name,
                'level': guild.level,
                'experience': guild.experience,
                'member_count': guild.members.count(),
                'max_members': guild.max_members,
                'crystal_balance': guild.crystal_balance,
                'exon_balance': guild.exon_balance,
                'stats': {
                    'gates_cleared': guild.total_gates_cleared,
                    'quests_completed': guild.total_quests_completed,
                    'boss_kills': guild.total_boss_kills,
                    'weekly_activity': guild.weekly_activity
                },
                'members': [
                    {
                        'id': member.character_id,
                        'rank': member.rank.value,
                        'contribution': member.contribution_points,
                        'weekly_contribution': member.weekly_contribution,
                        'joined_at': member.joined_at.isoformat()
                    }
                    for member in guild.members
                ]
            }
            data['guilds'].append(guild_data)
        
        # Get party data
        active_parties = Party.query.filter_by(status='active').all()
        for party in active_parties:
            party_data = {
                'id': party.id,
                'name': party.name,
                'leader_id': party.leader_id,
                'average_level': party.average_level,
                'total_luck': party.total_luck,
                'current_gate_id': party.current_gate_id,
                'created_at': party.created_at.isoformat(),
                'members': [
                    {
                        'id': member.character_id,
                        'damage_dealt': member.damage_dealt,
                        'damage_taken': member.damage_taken,
                        'healing_done': member.healing_done,
                        'deaths': member.deaths,
                        'contribution_score': member.contribution_score
                    }
                    for member in party.members
                ]
            }
            data['parties'].append(party_data)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_dir = project_root / 'data' / 'social'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        data_file = data_dir / f'social_data_{timestamp}.json'
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Social data exported to: {data_file}")

def main():
    parser = argparse.ArgumentParser(description="Terminusa Online Social Management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Guilds command
    guilds_parser = subparsers.add_parser('guilds',
                                        help='Check guild status')
    
    # Parties command
    parties_parser = subparsers.add_parser('parties',
                                         help='Analyze party activity')
    parties_parser.add_argument('--days', type=int, default=7,
                              help='Days of history to analyze')
    
    # Quests command
    quests_parser = subparsers.add_parser('quests',
                                        help='Manage guild quests')
    quests_parser.add_argument('--guild', help='Specific guild to manage')
    quests_parser.add_argument('--view-only', action='store_true',
                             help='Only view quests')
    
    # Export command
    export_parser = subparsers.add_parser('export',
                                        help='Export social data')
    
    args = parser.parse_args()
    
    if args.command == 'guilds':
        check_guilds(args)
    elif args.command == 'parties':
        analyze_parties(args)
    elif args.command == 'quests':
        manage_quests(args)
    elif args.command == 'export':
        export_social_data(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
