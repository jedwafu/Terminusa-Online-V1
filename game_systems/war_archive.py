from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
import gzip
from pathlib import Path

from models import db, Guild, GuildWar, WarTerritory, WarEvent, WarParticipant
from models.guild_war import WarStatus
from game_systems.event_system import EventSystem, EventType, GameEvent

class WarArchive:
    def __init__(self, websocket, archive_dir: str = 'data/war_archives'):
        self.event_system = EventSystem(websocket)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Archive settings
        self.ARCHIVE_AFTER_DAYS = 7
        self.COMPRESS_ARCHIVES = True
        self.KEEP_ARCHIVES_DAYS = 90

    def archive_war(self, war: GuildWar) -> Dict:
        """Archive a completed war"""
        try:
            # Create archive data structure
            archive_data = {
                'war_id': war.id,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': self._create_war_metadata(war),
                'participants': self._create_participants_data(war),
                'territories': self._create_territories_data(war),
                'events': self._create_events_data(war),
                'statistics': self._calculate_war_statistics(war)
            }

            # Create archive file
            archive_path = self._get_archive_path(war)
            self._save_archive(archive_path, archive_data)

            # Clean up war data from main database
            self._cleanup_war_data(war)

            # Emit archive creation event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                data={
                    'type': 'war_archived',
                    'war_id': war.id,
                    'archive_path': str(archive_path)
                }
            ))

            return {
                "success": True,
                "message": "War archived successfully",
                "archive_path": str(archive_path)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to archive war: {str(e)}"
            }

    def get_archived_war(self, war_id: int) -> Optional[Dict]:
        """Retrieve archived war data"""
        try:
            archive_path = self._find_archive(war_id)
            if not archive_path:
                return None

            return self._load_archive(archive_path)

        except Exception as e:
            print(f"Failed to retrieve archived war: {str(e)}")
            return None

    def get_guild_war_history(self, guild_id: int, 
                            page: int = 1, per_page: int = 10) -> Dict:
        """Get guild's war history from archives"""
        try:
            archives = []
            for archive_path in self.archive_dir.glob('*.json*'):
                try:
                    archive = self._load_archive(archive_path)
                    if guild_id in [
                        archive['metadata']['challenger_id'],
                        archive['metadata']['target_id']
                    ]:
                        archives.append(archive)
                except Exception as e:
                    print(f"Failed to load archive {archive_path}: {str(e)}")

            # Sort by timestamp descending
            archives.sort(key=lambda x: x['timestamp'], reverse=True)

            # Paginate results
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_archives = archives[start_idx:end_idx]

            return {
                "success": True,
                "total": len(archives),
                "page": page,
                "per_page": per_page,
                "wars": paginated_archives
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get war history: {str(e)}"
            }

    def cleanup_old_archives(self) -> Dict:
        """Clean up archives older than KEEP_ARCHIVES_DAYS"""
        try:
            cleanup_date = datetime.utcnow() - timedelta(days=self.KEEP_ARCHIVES_DAYS)
            cleaned = 0

            for archive_path in self.archive_dir.glob('*.json*'):
                try:
                    archive = self._load_archive(archive_path)
                    archive_date = datetime.fromisoformat(archive['timestamp'])
                    
                    if archive_date < cleanup_date:
                        archive_path.unlink()
                        cleaned += 1
                except Exception as e:
                    print(f"Failed to process archive {archive_path}: {str(e)}")

            return {
                "success": True,
                "message": f"Cleaned up {cleaned} old archives",
                "cleaned": cleaned
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clean up archives: {str(e)}"
            }

    def _create_war_metadata(self, war: GuildWar) -> Dict:
        """Create war metadata for archive"""
        return {
            'challenger_id': war.challenger_id,
            'challenger_name': war.challenger.name,
            'target_id': war.target_id,
            'target_name': war.target.name,
            'start_time': war.start_time.isoformat(),
            'end_time': war.end_time.isoformat(),
            'status': war.status,
            'winner_id': war.winner_id,
            'winner_name': war.winner.name if war.winner else None,
            'scores': war.scores
        }

    def _create_participants_data(self, war: GuildWar) -> Dict:
        """Create participants data for archive"""
        participants_data = {}
        for participant in war.participants_data:
            participants_data[participant.user_id] = {
                'username': participant.user.username,
                'guild_id': participant.guild_id,
                'points_contributed': participant.points_contributed,
                'kills': participant.kills,
                'deaths': participant.deaths,
                'territories_captured': participant.territories_captured,
                'stats': participant.stats
            }
        return participants_data

    def _create_territories_data(self, war: GuildWar) -> List[Dict]:
        """Create territories data for archive"""
        return [{
            'id': t.id,
            'name': t.name,
            'type': t.type,
            'status': t.status,
            'controller_id': t.controller_id,
            'position_x': t.position_x,
            'position_y': t.position_y,
            'bonuses': t.bonuses,
            'defense_data': t.defense_data
        } for t in war.territories]

    def _create_events_data(self, war: GuildWar) -> List[Dict]:
        """Create events data for archive"""
        return [{
            'id': e.id,
            'type': e.type,
            'initiator_id': e.initiator_id,
            'initiator_name': e.initiator.username if e.initiator else None,
            'target_id': e.target_id,
            'points': e.points,
            'details': e.details,
            'created_at': e.created_at.isoformat()
        } for e in war.events]

    def _calculate_war_statistics(self, war: GuildWar) -> Dict:
        """Calculate additional statistics for archive"""
        return {
            'duration': (war.end_time - war.start_time).total_seconds(),
            'total_participants': len(war.participants_data),
            'total_events': len(war.events),
            'territory_control': self._calculate_territory_control(war),
            'top_contributors': self._get_top_contributors(war),
            'event_breakdown': self._calculate_event_breakdown(war)
        }

    def _calculate_territory_control(self, war: GuildWar) -> Dict:
        """Calculate territory control statistics"""
        control_stats = {
            str(war.challenger_id): 0,
            str(war.target_id): 0,
            'neutral': 0
        }
        
        for territory in war.territories:
            if territory.controller_id:
                control_stats[str(territory.controller_id)] += 1
            else:
                control_stats['neutral'] += 1
                
        return control_stats

    def _get_top_contributors(self, war: GuildWar) -> Dict:
        """Get top contributors by different metrics"""
        participants = war.participants_data
        return {
            'points': sorted(
                participants, 
                key=lambda p: p.points_contributed, 
                reverse=True
            )[:5],
            'kills': sorted(
                participants, 
                key=lambda p: p.kills, 
                reverse=True
            )[:5],
            'territories': sorted(
                participants, 
                key=lambda p: p.territories_captured, 
                reverse=True
            )[:5]
        }

    def _calculate_event_breakdown(self, war: GuildWar) -> Dict:
        """Calculate breakdown of event types"""
        breakdown = {}
        for event in war.events:
            breakdown[event.type] = breakdown.get(event.type, 0) + 1
        return breakdown

    def _get_archive_path(self, war: GuildWar) -> Path:
        """Get path for war archive file"""
        filename = f"war_{war.id}_{war.end_time.strftime('%Y%m%d')}"
        if self.COMPRESS_ARCHIVES:
            return self.archive_dir / f"{filename}.json.gz"
        return self.archive_dir / f"{filename}.json"

    def _save_archive(self, path: Path, data: Dict) -> None:
        """Save archive data to file"""
        if self.COMPRESS_ARCHIVES:
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

    def _load_archive(self, path: Path) -> Dict:
        """Load archive data from file"""
        if path.suffix == '.gz':
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _find_archive(self, war_id: int) -> Optional[Path]:
        """Find archive file for war ID"""
        for path in self.archive_dir.glob(f"war_{war_id}_*.json*"):
            return path
        return None

    def _cleanup_war_data(self, war: GuildWar) -> None:
        """Clean up war data from main database"""
        try:
            # Delete related records
            WarEvent.query.filter_by(war_id=war.id).delete()
            WarTerritory.query.filter_by(war_id=war.id).delete()
            WarParticipant.query.filter_by(war_id=war.id).delete()
            
            # Delete war record
            db.session.delete(war)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to clean up war data: {str(e)}")
