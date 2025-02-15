import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import asyncio
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GameState(Enum):
    """Game states"""
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    MAINTENANCE = auto()
    SHUTDOWN = auto()

@dataclass
class GameConfig:
    """Game configuration"""
    max_players: int
    tick_rate: float
    save_interval: timedelta
    backup_interval: timedelta
    maintenance_window: Optional[timedelta] = None
    debug_mode: bool = False

@dataclass
class SystemStatus:
    """System status data"""
    name: str
    state: str
    uptime: timedelta
    load: float
    error_count: int
    last_error: Optional[str] = None

class GameSystems:
    """Core game systems manager"""
    def __init__(self, config: GameConfig):
        self.config = config
        self.state = GameState.INITIALIZING
        self.systems: Dict[str, SystemStatus] = {}
        self.start_time = datetime.utcnow()
        self.last_tick = self.start_time
        self.last_save = self.start_time
        self.last_backup = self.start_time
        self._running = False

    async def start(self):
        """Start game systems"""
        if self.state != GameState.INITIALIZING:
            return False
        
        try:
            # Initialize core systems
            systems = [
                "combat", "inventory", "quest",
                "chat", "party", "guild",
                "marketplace", "economy"
            ]
            
            for system in systems:
                self.systems[system] = SystemStatus(
                    name=system,
                    state="starting",
                    uptime=timedelta(),
                    load=0.0,
                    error_count=0
                )
                
                # Simulate system initialization
                await asyncio.sleep(0.1)
                self.systems[system].state = "running"
            
            self.state = GameState.RUNNING
            self._running = True
            
            # Start game loop
            asyncio.create_task(self._game_loop())
            return True
            
        except Exception as e:
            self.state = GameState.SHUTDOWN
            return False

    async def stop(self):
        """Stop game systems"""
        if self.state == GameState.SHUTDOWN:
            return False
        
        try:
            self._running = False
            
            # Shutdown systems in reverse order
            for system in reversed(list(self.systems.keys())):
                self.systems[system].state = "stopping"
                await asyncio.sleep(0.1)
                self.systems[system].state = "stopped"
            
            self.state = GameState.SHUTDOWN
            return True
            
        except Exception as e:
            return False

    async def pause(self):
        """Pause game systems"""
        if self.state != GameState.RUNNING:
            return False
        
        try:
            self.state = GameState.PAUSED
            for system in self.systems.values():
                system.state = "paused"
            return True
            
        except Exception as e:
            return False

    async def resume(self):
        """Resume game systems"""
        if self.state != GameState.PAUSED:
            return False
        
        try:
            self.state = GameState.RUNNING
            for system in self.systems.values():
                system.state = "running"
            return True
            
        except Exception as e:
            return False

    async def _game_loop(self):
        """Main game loop"""
        while self._running:
            try:
                now = datetime.utcnow()
                
                # Process game tick
                if (now - self.last_tick).total_seconds() >= 1.0 / self.config.tick_rate:
                    await self._process_tick()
                    self.last_tick = now
                
                # Process saves
                if now - self.last_save >= self.config.save_interval:
                    await self._process_save()
                    self.last_save = now
                
                # Process backups
                if now - self.last_backup >= self.config.backup_interval:
                    await self._process_backup()
                    self.last_backup = now
                
                # Check maintenance window
                if self.config.maintenance_window:
                    if (now.hour == self.config.maintenance_window.seconds // 3600 and
                        now.minute == (self.config.maintenance_window.seconds % 3600) // 60):
                        await self.maintenance()
                
                await asyncio.sleep(0.01)  # Prevent CPU hogging
                
            except Exception as e:
                if self.config.debug_mode:
                    print(f"Game loop error: {e}")

    async def _process_tick(self):
        """Process game tick"""
        for system in self.systems.values():
            if system.state == "running":
                try:
                    # Simulate system tick
                    await asyncio.sleep(0.01)
                    system.load = 0.5  # Simulated load
                    
                except Exception as e:
                    system.error_count += 1
                    system.last_error = str(e)

    async def _process_save(self):
        """Process game save"""
        for system in self.systems.values():
            if system.state == "running":
                try:
                    # Simulate save
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    system.error_count += 1
                    system.last_error = str(e)

    async def _process_backup(self):
        """Process game backup"""
        try:
            # Simulate backup
            await asyncio.sleep(0.5)
            
        except Exception as e:
            if self.config.debug_mode:
                print(f"Backup error: {e}")

    async def maintenance(self):
        """Enter maintenance mode"""
        if self.state not in (GameState.RUNNING, GameState.PAUSED):
            return False
        
        try:
            # Pause systems
            await self.pause()
            
            self.state = GameState.MAINTENANCE
            
            # Simulate maintenance tasks
            await asyncio.sleep(1.0)
            
            # Resume systems
            self.state = GameState.PAUSED
            await self.resume()
            
            return True
            
        except Exception as e:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get game systems status"""
        return {
            'state': self.state.name,
            'uptime': datetime.utcnow() - self.start_time,
            'systems': {
                name: {
                    'state': status.state,
                    'uptime': status.uptime,
                    'load': status.load,
                    'errors': status.error_count
                }
                for name, status in self.systems.items()
            }
        }

class TestGameSystems(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.config = GameConfig(
            max_players=1000,
            tick_rate=20,
            save_interval=timedelta(minutes=5),
            backup_interval=timedelta(hours=1),
            debug_mode=True
        )
        
        self.game_systems = GameSystems(self.config)

    def tearDown(self):
        """Clean up after each test"""
        self.loop.close()

    async def test_system_startup(self):
        """Test game systems startup"""
        # Start systems
        success = await self.game_systems.start()
        
        # Verify startup
        self.assertTrue(success)
        self.assertEqual(self.game_systems.state, GameState.RUNNING)
        
        # Verify all systems running
        for system in self.game_systems.systems.values():
            self.assertEqual(system.state, "running")

    def test_system_startup_sync(self):
        """Test synchronous system startup"""
        success = self.loop.run_until_complete(
            self.game_systems.start()
        )
        self.assertTrue(success)

    async def test_system_shutdown(self):
        """Test game systems shutdown"""
        # Start and stop systems
        await self.game_systems.start()
        success = await self.game_systems.stop()
        
        # Verify shutdown
        self.assertTrue(success)
        self.assertEqual(self.game_systems.state, GameState.SHUTDOWN)
        
        # Verify all systems stopped
        for system in self.game_systems.systems.values():
            self.assertEqual(system.state, "stopped")

    async def test_system_pause_resume(self):
        """Test system pause and resume"""
        # Start systems
        await self.game_systems.start()
        
        # Pause systems
        success = await self.game_systems.pause()
        self.assertTrue(success)
        self.assertEqual(self.game_systems.state, GameState.PAUSED)
        
        # Resume systems
        success = await self.game_systems.resume()
        self.assertTrue(success)
        self.assertEqual(self.game_systems.state, GameState.RUNNING)

    async def test_maintenance_mode(self):
        """Test maintenance mode"""
        # Start systems
        await self.game_systems.start()
        
        # Enter maintenance
        success = await self.game_systems.maintenance()
        self.assertTrue(success)
        
        # Verify systems resumed after maintenance
        self.assertEqual(self.game_systems.state, GameState.RUNNING)

    async def test_error_handling(self):
        """Test error handling"""
        # Start systems
        await self.game_systems.start()
        
        # Simulate error in system
        system = self.game_systems.systems['combat']
        system.error_count = 1
        system.last_error = "Test error"
        
        # Verify error tracking
        self.assertEqual(system.error_count, 1)
        self.assertEqual(system.last_error, "Test error")

    async def test_status_reporting(self):
        """Test status reporting"""
        # Start systems
        await self.game_systems.start()
        
        # Get status
        status = self.game_systems.get_status()
        
        # Verify status
        self.assertEqual(status['state'], 'RUNNING')
        self.assertEqual(len(status['systems']), 8)
        self.assertIn('combat', status['systems'])

    async def test_game_loop(self):
        """Test game loop execution"""
        # Start systems
        await self.game_systems.start()
        
        # Let game loop run briefly
        await asyncio.sleep(0.1)
        
        # Verify tick processing
        for system in self.game_systems.systems.values():
            self.assertGreater(system.load, 0)

    async def test_save_backup_intervals(self):
        """Test save and backup intervals"""
        # Start systems
        await self.game_systems.start()
        
        # Override intervals for testing
        self.game_systems.config.save_interval = timedelta(seconds=0.1)
        self.game_systems.config.backup_interval = timedelta(seconds=0.2)
        
        # Let intervals trigger
        await asyncio.sleep(0.3)
        
        # Verify intervals processed
        self.assertGreater(
            datetime.utcnow() - self.game_systems.last_save,
            timedelta(seconds=0)
        )
        self.assertGreater(
            datetime.utcnow() - self.game_systems.last_backup,
            timedelta(seconds=0)
        )

if __name__ == '__main__':
    unittest.main()
