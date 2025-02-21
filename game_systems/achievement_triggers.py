from typing import Dict, Any
from datetime import datetime

from models import db, Guild, User
from game_systems.achievement_system import AchievementSystem
from game_systems.event_system import EventSystem, EventType, GameEvent

class AchievementTriggers:
    def __init__(self, websocket):
        self.achievement_system = AchievementSystem(websocket)
        self.event_system = EventSystem(websocket)

    def handle_gate_clear(self, guild: Guild, gate_data: Dict[str, Any]) -> None:
        """Handle gate clear achievement triggers"""
        try:
            # Check gates cleared achievement
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='gates_cleared',
                value=guild.total_gates_cleared
            )

            # Check specific gate rank achievements if applicable
            if gate_data.get('rank') in ['S', 'A']:
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type=f'{gate_data["rank"]}_rank_gates',
                    value=guild.gates_cleared_by_rank.get(gate_data['rank'], 0)
                )

            # Check party size achievements
            party_size = len(gate_data.get('party_members', []))
            if party_size >= 5:
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='full_party_clears',
                    value=guild.full_party_clears
                )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle gate clear achievements: {str(e)}")

    def handle_quest_completion(self, guild: Guild, quest_data: Dict[str, Any]) -> None:
        """Handle quest completion achievement triggers"""
        try:
            # Check quest completion achievements
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='quests_completed',
                value=guild.quests.filter_by(status='completed').count()
            )

            # Check quest difficulty achievements
            if quest_data.get('difficulty') == 'extreme':
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='extreme_quests',
                    value=guild.quests.filter_by(
                        status='completed',
                        difficulty='extreme'
                    ).count()
                )

            # Check quest participation achievements
            participant_count = len(quest_data.get('participants', {}))
            if participant_count >= 10:
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='mass_participation',
                    value=guild.mass_participation_quests
                )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle quest completion achievements: {str(e)}")

    def handle_member_update(self, guild: Guild, member_data: Dict[str, Any]) -> None:
        """Handle member-related achievement triggers"""
        try:
            # Check member count achievements
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='member_count',
                value=len(guild.active_members)
            )

            # Check high level member achievements
            high_level_count = sum(1 for m in guild.active_members if m.user.level >= 50)
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='high_level_members',
                value=high_level_count
            )

            # Check class diversity achievements
            unique_classes = len(set(m.user.job_class for m in guild.active_members))
            if unique_classes >= 5:
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='class_diversity',
                    value=unique_classes
                )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle member update achievements: {str(e)}")

    def handle_treasury_update(self, guild: Guild, transaction_data: Dict[str, Any]) -> None:
        """Handle treasury-related achievement triggers"""
        try:
            # Check crystal balance achievements
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='crystal_balance',
                value=int(guild.crystal_balance)
            )

            # Check exon balance achievements
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='exon_balance',
                value=float(guild.exon_balance)
            )

            # Check transaction volume achievements
            if transaction_data.get('type') == 'market_transaction':
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='market_volume',
                    value=guild.market_transaction_volume
                )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle treasury update achievements: {str(e)}")

    def handle_guild_level_up(self, guild: Guild, level_data: Dict[str, Any]) -> None:
        """Handle guild level-up achievement triggers"""
        try:
            # Check guild level achievements
            self.achievement_system.check_achievements(
                guild=guild,
                trigger_type='guild_level',
                value=guild.level
            )

            # Check rapid growth achievements
            days_since_creation = (datetime.utcnow() - guild.created_at).days
            if days_since_creation <= 30 and guild.level >= 25:
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='rapid_growth',
                    value=guild.level
                )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle guild level-up achievements: {str(e)}")

    def handle_combat_event(self, guild: Guild, combat_data: Dict[str, Any]) -> None:
        """Handle combat-related achievement triggers"""
        try:
            # Check magic beast kills
            if combat_data.get('type') == 'beast_kill':
                beast_data = combat_data.get('beast', {})
                
                # Check high rank beast achievements
                if beast_data.get('rank') in ['S', 'A']:
                    self.achievement_system.check_achievements(
                        guild=guild,
                        trigger_type='high_rank_beasts',
                        value=guild.high_rank_beast_kills
                    )

                # Check monarch beast achievements
                if beast_data.get('is_monarch', False):
                    self.achievement_system.check_achievements(
                        guild=guild,
                        trigger_type='monarch_beasts',
                        value=guild.monarch_beast_kills
                    )

            # Check party survival achievements
            if combat_data.get('type') == 'gate_clear':
                if not combat_data.get('casualties', False):
                    self.achievement_system.check_achievements(
                        guild=guild,
                        trigger_type='perfect_clears',
                        value=guild.perfect_gate_clears
                    )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle combat event achievements: {str(e)}")

    def handle_special_event(self, guild: Guild, event_data: Dict[str, Any]) -> None:
        """Handle special event achievement triggers"""
        try:
            event_type = event_data.get('type')
            
            if event_type == 'guild_war':
                # Check guild war achievements
                if event_data.get('result') == 'victory':
                    self.achievement_system.check_achievements(
                        guild=guild,
                        trigger_type='guild_war_victories',
                        value=guild.guild_war_wins
                    )

            elif event_type == 'territory_control':
                # Check territory control achievements
                controlled_territories = event_data.get('controlled_territories', 0)
                self.achievement_system.check_achievements(
                    guild=guild,
                    trigger_type='territory_control',
                    value=controlled_territories
                )

            elif event_type == 'seasonal_ranking':
                # Check seasonal ranking achievements
                rank = event_data.get('rank', 0)
                if rank <= 10:
                    self.achievement_system.check_achievements(
                        guild=guild,
                        trigger_type='top_ranking',
                        value=rank
                    )

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to handle special event achievements: {str(e)}")
