from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random

from models import db, Guild, GuildWar, WarTerritory, WarEvent, User
from models.guild_war import TerritoryType, TerritoryStatus
from game_systems.event_system import EventSystem, EventType, GameEvent

class TerritoryControl:
    def __init__(self, websocket):
        self.event_system = EventSystem(websocket)

        # Territory configuration
        self.TERRITORY_TYPES = {
            TerritoryType.GATE: {
                'capture_time': 300,  # seconds
                'defense_bonus': 1.2,
                'reward_multiplier': 1.5,
                'points_per_tick': 5
            },
            TerritoryType.RESOURCE: {
                'capture_time': 180,
                'defense_bonus': 1.1,
                'reward_multiplier': 1.3,
                'points_per_tick': 3
            },
            TerritoryType.STRONGHOLD: {
                'capture_time': 600,
                'defense_bonus': 1.5,
                'reward_multiplier': 2.0,
                'points_per_tick': 10
            },
            TerritoryType.OUTPOST: {
                'capture_time': 120,
                'defense_bonus': 1.0,
                'reward_multiplier': 1.0,
                'points_per_tick': 2
            }
        }

    def generate_territories(self, war: GuildWar) -> List[WarTerritory]:
        """Generate territories for a new war"""
        territories = []
        map_size = (1000, 1000)  # Virtual map size
        min_distance = 100  # Minimum distance between territories

        # Territory distribution
        territory_counts = {
            TerritoryType.GATE: 5,
            TerritoryType.RESOURCE: 8,
            TerritoryType.STRONGHOLD: 3,
            TerritoryType.OUTPOST: 6
        }

        positions = []
        for type_enum, count in territory_counts.items():
            for i in range(count):
                # Keep trying until we find a valid position
                while True:
                    x = random.randint(50, map_size[0] - 50)
                    y = random.randint(50, map_size[1] - 50)
                    
                    # Check minimum distance from other territories
                    if all(self._calculate_distance(x, y, px, py) >= min_distance 
                          for px, py in positions):
                        positions.append((x, y))
                        
                        territory = WarTerritory(
                            war_id=war.id,
                            name=f"{type_enum.value.title()} {i+1}",
                            type=type_enum.value,
                            status=TerritoryStatus.NEUTRAL.value,
                            position_x=x / map_size[0],  # Normalize to 0-1
                            position_y=y / map_size[1],  # Normalize to 0-1
                            bonuses=self._generate_territory_bonuses(type_enum),
                            defense_data={
                                'base_defense': self.TERRITORY_TYPES[type_enum]['defense_bonus'],
                                'reinforcements': 0,
                                'last_attack': None
                            }
                        )
                        territories.append(territory)
                        break

        return territories

    def initiate_attack(self, territory: WarTerritory, attacker: User, 
                       attacking_force: int) -> Dict:
        """Initiate an attack on a territory"""
        try:
            if not self._can_attack(territory, attacker):
                return {
                    "success": False,
                    "message": "Cannot attack this territory"
                }

            war = GuildWar.query.get(territory.war_id)
            if not war or not war.is_active:
                return {
                    "success": False,
                    "message": "War is not active"
                }

            # Calculate attack success chance
            success_chance = self._calculate_attack_chance(
                territory, attacker, attacking_force
            )

            # Determine attack outcome
            is_successful = random.random() < success_chance
            
            if is_successful:
                # Update territory control
                old_controller = territory.controller_id
                territory.controller_id = attacker.guild_id
                territory.status = TerritoryStatus.FRIENDLY.value
                territory.defense_data['reinforcements'] = attacking_force
                territory.defense_data['last_attack'] = datetime.utcnow().isoformat()

                # Award points
                points = self._calculate_capture_points(territory)
                war.update_score(attacker.guild_id, points)

                # Create war event
                event = WarEvent(
                    war_id=war.id,
                    type='territory_capture',
                    initiator_id=attacker.id,
                    target_id=territory.id,
                    points=points,
                    details={
                        'territory_name': territory.name,
                        'territory_type': territory.type,
                        'old_controller': old_controller,
                        'attacking_force': attacking_force
                    }
                )
                db.session.add(event)

            else:
                # Record failed attack
                territory.defense_data['last_attack'] = datetime.utcnow().isoformat()
                event = WarEvent(
                    war_id=war.id,
                    type='territory_attack_failed',
                    initiator_id=attacker.id,
                    target_id=territory.id,
                    points=0,
                    details={
                        'territory_name': territory.name,
                        'territory_type': territory.type,
                        'attacking_force': attacking_force
                    }
                )
                db.session.add(event)

            db.session.commit()

            # Emit territory update event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=attacker.guild_id,
                data={
                    'type': 'territory_update',
                    'territory': territory.to_dict(),
                    'success': is_successful,
                    'points': points if is_successful else 0
                }
            ))

            return {
                "success": True,
                "message": "Territory captured!" if is_successful else "Attack failed!",
                "points_gained": points if is_successful else 0
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to process attack: {str(e)}"
            }

    def reinforce_territory(self, territory: WarTerritory, user: User, 
                          reinforcement_amount: int) -> Dict:
        """Reinforce a controlled territory"""
        try:
            if territory.controller_id != user.guild_id:
                return {
                    "success": False,
                    "message": "Can only reinforce own territories"
                }

            war = GuildWar.query.get(territory.war_id)
            if not war or not war.is_active:
                return {
                    "success": False,
                    "message": "War is not active"
                }

            # Update defense data
            territory.defense_data['reinforcements'] += reinforcement_amount
            territory.defense_data['last_reinforced'] = datetime.utcnow().isoformat()

            # Create war event
            event = WarEvent(
                war_id=war.id,
                type='territory_reinforce',
                initiator_id=user.id,
                target_id=territory.id,
                points=0,
                details={
                    'territory_name': territory.name,
                    'reinforcement_amount': reinforcement_amount
                }
            )
            db.session.add(event)
            db.session.commit()

            # Emit territory update event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=user.guild_id,
                data={
                    'type': 'territory_update',
                    'territory': territory.to_dict()
                }
            ))

            return {
                "success": True,
                "message": "Territory reinforced successfully"
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to reinforce territory: {str(e)}"
            }

    def process_territory_tick(self, war: GuildWar) -> None:
        """Process periodic territory updates"""
        try:
            for territory in war.territories:
                if territory.controller_id:
                    # Award points for controlled territories
                    points = self._calculate_tick_points(territory)
                    war.update_score(territory.controller_id, points)

                    # Decay reinforcements over time
                    if territory.defense_data.get('reinforcements', 0) > 0:
                        territory.defense_data['reinforcements'] *= 0.95  # 5% decay

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to process territory tick: {str(e)}")

    def _calculate_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate distance between two points"""
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def _generate_territory_bonuses(self, territory_type: TerritoryType) -> Dict:
        """Generate bonuses for a territory based on its type"""
        base_bonuses = self.TERRITORY_TYPES[territory_type]
        return {
            'capture_time': base_bonuses['capture_time'],
            'defense_bonus': base_bonuses['defense_bonus'],
            'reward_multiplier': base_bonuses['reward_multiplier']
        }

    def _can_attack(self, territory: WarTerritory, attacker: User) -> bool:
        """Check if user can attack territory"""
        # Can't attack own territory
        if territory.controller_id == attacker.guild_id:
            return False

        # Check cooldown from last attack
        if territory.defense_data.get('last_attack'):
            last_attack = datetime.fromisoformat(territory.defense_data['last_attack'])
            if datetime.utcnow() - last_attack < timedelta(minutes=5):
                return False

        return True

    def _calculate_attack_chance(self, territory: WarTerritory, attacker: User, 
                               attacking_force: int) -> float:
        """Calculate chance of successful attack"""
        base_chance = 0.5
        
        # Adjust for territory defenses
        defense_force = territory.defense_data.get('reinforcements', 0)
        defense_bonus = territory.defense_data.get('base_defense', 1.0)
        total_defense = defense_force * defense_bonus

        # Calculate force ratio
        force_ratio = attacking_force / max(1, total_defense)
        
        # Adjust base chance
        success_chance = base_chance * force_ratio
        
        # Cap between 0.1 and 0.9
        return max(0.1, min(0.9, success_chance))

    def _calculate_capture_points(self, territory: WarTerritory) -> int:
        """Calculate points for capturing a territory"""
        base_points = {
            TerritoryType.GATE.value: 100,
            TerritoryType.RESOURCE.value: 75,
            TerritoryType.STRONGHOLD.value: 150,
            TerritoryType.OUTPOST.value: 50
        }
        
        return int(base_points[territory.type] * 
                  territory.bonuses.get('reward_multiplier', 1.0))

    def _calculate_tick_points(self, territory: WarTerritory) -> int:
        """Calculate points for holding a territory per tick"""
        return self.TERRITORY_TYPES[TerritoryType(territory.type)]['points_per_tick']
