import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict
import threading
import logging

from models import db, Guild, GuildWar, WarTerritory
from models.guild_war import WarStatus
from game_systems.territory_control import TerritoryControl
from game_systems.event_system import EventSystem, EventType, GameEvent
from scripts.init_guild_war import GuildWarInitializer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WarScheduler:
    def __init__(self, websocket):
        self.territory_control = TerritoryControl(websocket)
        self.event_system = EventSystem(websocket)
        self.war_initializer = GuildWarInitializer(websocket)
        
        # Scheduler intervals
        self.WAR_CHECK_INTERVAL = 60  # seconds
        self.TERRITORY_UPDATE_INTERVAL = 300  # seconds
        self.CLEANUP_INTERVAL = 3600  # seconds

        # Initialize schedules
        self.init_schedules()

    def init_schedules(self):
        """Initialize all scheduled tasks"""
        schedule.every(self.WAR_CHECK_INTERVAL).seconds.do(self.check_wars)
        schedule.every(self.TERRITORY_UPDATE_INTERVAL).seconds.do(self.update_territories)
        schedule.every(self.CLEANUP_INTERVAL).seconds.do(self.cleanup_old_wars)

    def run(self):
        """Run the scheduler in a separate thread"""
        thread = threading.Thread(target=self._run_continuously)
        thread.daemon = True
        thread.start()
        logger.info("War scheduler started")

    def _run_continuously(self):
        """Run scheduler continuously"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def check_wars(self):
        """Check and update war statuses"""
        try:
            now = datetime.utcnow()
            
            # Check wars in preparation
            prep_wars = GuildWar.query.filter_by(
                status=WarStatus.PREPARATION.value
            ).filter(
                GuildWar.start_time <= now
            ).all()
            
            for war in prep_wars:
                try:
                    self.war_initializer.start_war(war)
                    logger.info(f"Started war {war.id} between {war.challenger.name} and {war.target.name}")
                except Exception as e:
                    logger.error(f"Failed to start war {war.id}: {str(e)}")
            
            # Check active wars
            active_wars = GuildWar.query.filter_by(
                status=WarStatus.ACTIVE.value
            ).filter(
                GuildWar.end_time <= now
            ).all()
            
            for war in active_wars:
                try:
                    self.war_initializer.end_war(war)
                    logger.info(f"Ended war {war.id}")
                except Exception as e:
                    logger.error(f"Failed to end war {war.id}: {str(e)}")

        except Exception as e:
            logger.error(f"War check error: {str(e)}")

    def update_territories(self):
        """Update territory statuses and points"""
        try:
            active_wars = GuildWar.query.filter_by(
                status=WarStatus.ACTIVE.value
            ).all()

            for war in active_wars:
                try:
                    self.territory_control.process_territory_tick(war)
                    self._check_territory_status_changes(war)
                    logger.info(f"Updated territories for war {war.id}")
                except Exception as e:
                    logger.error(f"Failed to update territories for war {war.id}: {str(e)}")

        except Exception as e:
            logger.error(f"Territory update error: {str(e)}")

    def cleanup_old_wars(self):
        """Clean up old war data"""
        try:
            cleanup_threshold = datetime.utcnow() - timedelta(days=7)
            
            old_wars = GuildWar.query.filter(
                GuildWar.end_time < cleanup_threshold,
                GuildWar.status.in_([
                    WarStatus.COMPLETED.value,
                    WarStatus.CANCELLED.value
                ])
            ).all()

            for war in old_wars:
                try:
                    self._archive_war_data(war)
                    logger.info(f"Archived war {war.id}")
                except Exception as e:
                    logger.error(f"Failed to archive war {war.id}: {str(e)}")

        except Exception as e:
            logger.error(f"War cleanup error: {str(e)}")

    def _check_territory_status_changes(self, war: GuildWar):
        """Check for territory status changes"""
        try:
            for territory in war.territories:
                old_status = territory.status
                new_status = self._calculate_territory_status(territory)
                
                if old_status != new_status:
                    territory.status = new_status
                    db.session.commit()
                    
                    # Emit territory update event
                    self.event_system.emit_event(GameEvent(
                        type=EventType.GUILD_UPDATE,
                        guild_id=territory.controller_id,
                        data={
                            'type': 'territory_status_change',
                            'territory': territory.to_dict(),
                            'old_status': old_status,
                            'new_status': new_status
                        }
                    ))

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to check territory status changes: {str(e)}")

    def _calculate_territory_status(self, territory: WarTerritory) -> str:
        """Calculate territory status based on recent activity"""
        try:
            recent_events = territory.war.events.filter(
                WarEvent.target_id == territory.id,
                WarEvent.created_at >= datetime.utcnow() - timedelta(minutes=5)
            ).all()

            if not recent_events:
                return territory.status

            # Count recent attacks from each guild
            attack_counts = {}
            for event in recent_events:
                if event.type == 'territory_attack':
                    guild_id = event.details.get('attacker_guild_id')
                    attack_counts[guild_id] = attack_counts.get(guild_id, 0) + 1

            # Determine if territory is contested
            if len(attack_counts) > 1:
                return WarStatus.CONTESTED.value

            return territory.status

        except Exception as e:
            logger.error(f"Failed to calculate territory status: {str(e)}")
            return territory.status

    def _archive_war_data(self, war: GuildWar):
        """Archive war data before cleanup"""
        try:
            # Create archive record
            archive_data = {
                'war_id': war.id,
                'challenger': war.challenger.name,
                'target': war.target.name,
                'start_time': war.start_time.isoformat(),
                'end_time': war.end_time.isoformat(),
                'winner': war.winner.name if war.winner else None,
                'scores': war.scores,
                'participants': war.participants,
                'territories': [t.to_dict() for t in war.territories],
                'events': [e.to_dict() for e in war.events]
            }

            # Store archive data (implement storage method as needed)
            self._store_archive(archive_data)

            # Clean up war data
            war.events.delete()
            war.territories.delete()
            db.session.delete(war)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to archive war data: {str(e)}")

    def _store_archive(self, archive_data: Dict):
        """Store archived war data"""
        # Implement storage method (e.g., file system, separate database, etc.)
        pass

# Scheduler instance
_scheduler = None

def init_scheduler(websocket):
    """Initialize the war scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = WarScheduler(websocket)
        _scheduler.run()
        logger.info("War scheduler initialized")
    return _scheduler

def get_scheduler():
    """Get the scheduler instance"""
    global _scheduler
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized")
    return _scheduler

if __name__ == "__main__":
    # For testing purposes
    from websocket_manager import WebSocketManager
    websocket = WebSocketManager()
    scheduler = init_scheduler(websocket)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
