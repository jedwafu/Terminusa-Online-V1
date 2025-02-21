from datetime import datetime, timedelta
import random

from models import db, Guild, GuildWar, WarTerritory, User
from models.guild_war import WarStatus, TerritoryType, TerritoryStatus
from game_systems.territory_control import TerritoryControl
from game_systems.event_system import EventSystem, EventType, GameEvent

class GuildWarInitializer:
    def __init__(self, websocket):
        self.territory_control = TerritoryControl(websocket)
        self.event_system = EventSystem(websocket)

    def initialize_war(self, challenger: Guild, target: Guild) -> GuildWar:
        """Initialize a new guild war"""
        try:
            # Create war record
            war = GuildWar(
                challenger_id=challenger.id,
                target_id=target.id,
                status=WarStatus.PREPARATION.value,
                start_time=datetime.utcnow() + timedelta(hours=24),  # 24h preparation
                end_time=datetime.utcnow() + timedelta(hours=72),    # 72h total duration
                participants={
                    str(challenger.id): [],
                    str(target.id): []
                },
                scores={
                    str(challenger.id): 0,
                    str(target.id): 0
                }
            )
            db.session.add(war)
            db.session.flush()  # Get war ID without committing

            # Generate territories
            territories = self.territory_control.generate_territories(war)
            for territory in territories:
                db.session.add(territory)

            db.session.commit()

            # Emit war initialization event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=challenger.id,
                data={
                    'type': 'war_initialized',
                    'war_id': war.id,
                    'challenger': challenger.name,
                    'target': target.name,
                    'preparation_ends': war.start_time.isoformat(),
                    'war_ends': war.end_time.isoformat()
                }
            ))

            return war

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to initialize war: {str(e)}")

    def start_war(self, war: GuildWar) -> bool:
        """Start a war after preparation period"""
        try:
            if war.status != WarStatus.PREPARATION.value:
                return False

            # Verify minimum participants
            min_participants = 10
            for guild_id, participants in war.participants.items():
                if len(participants) < min_participants:
                    self._cancel_war(war, f"Guild {guild_id} has insufficient participants")
                    return False

            # Update war status
            war.status = WarStatus.ACTIVE.value
            db.session.commit()

            # Emit war start event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                data={
                    'type': 'war_started',
                    'war_id': war.id,
                    'challenger': war.challenger.name,
                    'target': war.target.name,
                    'territories': [t.to_dict() for t in war.territories]
                }
            ))

            return True

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to start war: {str(e)}")

    def end_war(self, war: GuildWar) -> Dict:
        """End a war and determine winner"""
        try:
            if war.status != WarStatus.ACTIVE.value:
                return {
                    "success": False,
                    "message": "War is not active"
                }

            # Calculate final scores
            challenger_score = war.scores.get(str(war.challenger_id), 0)
            target_score = war.scores.get(str(war.target_id), 0)

            # Determine winner
            winner = war.challenger if challenger_score > target_score else war.target
            loser = war.target if challenger_score > target_score else war.challenger

            # Calculate rewards
            rewards = self._calculate_war_rewards(war, winner)

            # Update war record
            war.status = WarStatus.COMPLETED.value
            war.winner_id = winner.id
            war.rewards = rewards

            # Update guild stats
            winner.wars_won += 1
            winner.total_war_points += max(challenger_score, target_score)
            loser.wars_lost += 1
            loser.total_war_points += min(challenger_score, target_score)

            # Distribute rewards
            self._distribute_rewards(winner, rewards)

            db.session.commit()

            # Emit war end event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                data={
                    'type': 'war_ended',
                    'war_id': war.id,
                    'winner': winner.name,
                    'final_scores': war.scores,
                    'rewards': rewards
                }
            ))

            return {
                "success": True,
                "message": f"War ended. Winner: {winner.name}",
                "rewards": rewards
            }

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to end war: {str(e)}")

    def _calculate_war_rewards(self, war: GuildWar, winner: Guild) -> Dict:
        """Calculate rewards for war victory"""
        base_rewards = {
            'crystals': 50000,
            'exons': 500,
            'guild_exp': 5000
        }

        # Calculate multipliers based on war stats
        territory_multiplier = 1 + (len([t for t in war.territories 
            if t.controller_id == winner.id]) / len(war.territories))
        
        participation_multiplier = 1 + (len(war.participants[str(winner.id)]) / 50)  # Max 50 participants
        
        score_difference = abs(war.scores[str(war.challenger_id)] - 
                             war.scores[str(war.target_id)])
        dominance_multiplier = 1 + (score_difference / 10000)  # Bonus for decisive victory

        # Apply multipliers
        total_multiplier = (territory_multiplier + participation_multiplier + 
                          dominance_multiplier) / 3

        return {
            'crystals': int(base_rewards['crystals'] * total_multiplier),
            'exons': int(base_rewards['exons'] * total_multiplier),
            'guild_exp': int(base_rewards['guild_exp'] * total_multiplier),
            'multipliers': {
                'territory': territory_multiplier,
                'participation': participation_multiplier,
                'dominance': dominance_multiplier,
                'total': total_multiplier
            }
        }

    def _distribute_rewards(self, guild: Guild, rewards: Dict) -> None:
        """Distribute war rewards to winning guild"""
        try:
            # Add rewards to guild treasury
            guild.crystal_balance += rewards['crystals']
            guild.exon_balance += rewards['exons']
            
            # Add guild experience
            from game_systems.progression_system import ProgressionSystem
            progression_system = ProgressionSystem(self.event_system.websocket)
            progression_system.add_experience(
                guild=guild,
                amount=rewards['guild_exp'],
                source='guild_war_victory'
            )

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to distribute rewards: {str(e)}")

    def _cancel_war(self, war: GuildWar, reason: str) -> None:
        """Cancel a war"""
        try:
            war.status = WarStatus.CANCELLED.value
            db.session.commit()

            # Emit war cancelled event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                data={
                    'type': 'war_cancelled',
                    'war_id': war.id,
                    'reason': reason
                }
            ))

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to cancel war: {str(e)}")

# Background task to check and update war status
def check_war_status():
    """Check and update status of ongoing wars"""
    try:
        now = datetime.utcnow()
        
        # Find wars in preparation that should start
        prep_wars = GuildWar.query.filter_by(
            status=WarStatus.PREPARATION.value
        ).filter(
            GuildWar.start_time <= now
        ).all()
        
        for war in prep_wars:
            GuildWarInitializer(None).start_war(war)
        
        # Find active wars that should end
        active_wars = GuildWar.query.filter_by(
            status=WarStatus.ACTIVE.value
        ).filter(
            GuildWar.end_time <= now
        ).all()
        
        for war in active_wars:
            GuildWarInitializer(None).end_war(war)

    except Exception as e:
        print(f"Error in war status check: {str(e)}")
        db.session.rollback()
