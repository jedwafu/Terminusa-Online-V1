import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto
import json
import threading
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MaintenanceState(Enum):
    """Maintenance states"""
    INACTIVE = auto()
    SCHEDULED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()

class MaintenanceType(Enum):
    """Maintenance types"""
    UPDATE = auto()
    HOTFIX = auto()
    BACKUP = auto()
    CLEANUP = auto()
    RESTART = auto()
    EMERGENCY = auto()

@dataclass
class MaintenanceWindow:
    """Maintenance window data"""
    id: str
    type: MaintenanceType
    state: MaintenanceState
    start_time: datetime
    end_time: datetime
    description: str
    tasks: List[Dict[str, Any]]
    affected_services: List[str]
    notification_sent: bool = False
    progress: Optional[float] = None
    error: Optional[str] = None

class MaintenanceSystem:
    """System for managing server maintenance"""
    def __init__(self):
        self.maintenance_windows: Dict[str, MaintenanceWindow] = {}
        self.current_maintenance: Optional[str] = None
        self._lock = threading.Lock()
        self._maintenance_thread: Optional[threading.Thread] = None

    def schedule_maintenance(
        self,
        type: MaintenanceType,
        start_time: datetime,
        end_time: datetime,
        description: str,
        tasks: List[Dict[str, Any]],
        affected_services: List[str]
    ) -> MaintenanceWindow:
        """Schedule a maintenance window"""
        maintenance_id = f"maint_{int(time.time())}"
        
        window = MaintenanceWindow(
            id=maintenance_id,
            type=type,
            state=MaintenanceState.SCHEDULED,
            start_time=start_time,
            end_time=end_time,
            description=description,
            tasks=tasks,
            affected_services=affected_services
        )
        
        self.maintenance_windows[maintenance_id] = window
        return window

    def start_maintenance(self, maintenance_id: str) -> bool:
        """Start a maintenance window"""
        with self._lock:
            if self.current_maintenance:
                return False
            
            window = self.maintenance_windows.get(maintenance_id)
            if not window or window.state != MaintenanceState.SCHEDULED:
                return False
            
            window.state = MaintenanceState.IN_PROGRESS
            self.current_maintenance = maintenance_id
            
            # Start maintenance thread
            self._maintenance_thread = threading.Thread(
                target=self._run_maintenance,
                args=(window,)
            )
            self._maintenance_thread.start()
            
            return True

    def cancel_maintenance(self, maintenance_id: str) -> bool:
        """Cancel a scheduled maintenance"""
        with self._lock:
            window = self.maintenance_windows.get(maintenance_id)
            if not window or window.state != MaintenanceState.SCHEDULED:
                return False
            
            del self.maintenance_windows[maintenance_id]
            return True

    def get_maintenance_status(
        self,
        maintenance_id: str
    ) -> Optional[MaintenanceWindow]:
        """Get maintenance window status"""
        return self.maintenance_windows.get(maintenance_id)

    def get_active_maintenance(self) -> Optional[MaintenanceWindow]:
        """Get currently active maintenance"""
        if self.current_maintenance:
            return self.maintenance_windows.get(self.current_maintenance)
        return None

    def get_scheduled_maintenance(self) -> List[MaintenanceWindow]:
        """Get all scheduled maintenance windows"""
        return [
            window for window in self.maintenance_windows.values()
            if window.state == MaintenanceState.SCHEDULED
        ]

    def _run_maintenance(self, window: MaintenanceWindow):
        """Run maintenance tasks"""
        try:
            total_tasks = len(window.tasks)
            for i, task in enumerate(window.tasks, 1):
                # Execute task
                self._execute_task(task)
                
                # Update progress
                window.progress = (i / total_tasks) * 100
                
                # Check if we're past end time
                if datetime.utcnow() > window.end_time:
                    raise TimeoutError("Maintenance window exceeded")
            
            window.state = MaintenanceState.COMPLETED
            
        except Exception as e:
            window.state = MaintenanceState.FAILED
            window.error = str(e)
        
        finally:
            with self._lock:
                self.current_maintenance = None
                self._maintenance_thread = None

    def _execute_task(self, task: Dict[str, Any]):
        """Execute a maintenance task"""
        task_type = task.get('type')
        if task_type == 'service_stop':
            time.sleep(1)  # Simulate service stop
        elif task_type == 'backup':
            time.sleep(2)  # Simulate backup
        elif task_type == 'update':
            time.sleep(3)  # Simulate update
        elif task_type == 'service_start':
            time.sleep(1)  # Simulate service start
        else:
            raise ValueError(f"Unknown task type: {task_type}")

class TestMaintenance(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.maintenance = MaintenanceSystem()
        
        # Test maintenance window data
        self.start_time = datetime.utcnow() + timedelta(hours=1)
        self.end_time = self.start_time + timedelta(hours=2)
        self.tasks = [
            {'type': 'service_stop', 'service': 'game'},
            {'type': 'backup', 'target': 'database'},
            {'type': 'update', 'version': '1.1.0'},
            {'type': 'service_start', 'service': 'game'}
        ]
        self.affected_services = ['game', 'database']

    def test_maintenance_scheduling(self):
        """Test maintenance scheduling"""
        # Schedule maintenance
        window = self.maintenance.schedule_maintenance(
            MaintenanceType.UPDATE,
            self.start_time,
            self.end_time,
            "System update",
            self.tasks,
            self.affected_services
        )
        
        # Verify scheduling
        self.assertIsNotNone(window)
        self.assertEqual(window.state, MaintenanceState.SCHEDULED)
        
        # Check scheduled maintenance list
        scheduled = self.maintenance.get_scheduled_maintenance()
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(scheduled[0].id, window.id)

    def test_maintenance_execution(self):
        """Test maintenance execution"""
        # Schedule and start maintenance
        window = self.maintenance.schedule_maintenance(
            MaintenanceType.UPDATE,
            datetime.utcnow(),
            datetime.utcnow() + timedelta(hours=1),
            "System update",
            self.tasks,
            self.affected_services
        )
        
        success = self.maintenance.start_maintenance(window.id)
        self.assertTrue(success)
        
        # Wait for completion
        self._wait_for_maintenance()
        
        # Verify completion
        window = self.maintenance.get_maintenance_status(window.id)
        self.assertEqual(window.state, MaintenanceState.COMPLETED)
        self.assertEqual(window.progress, 100)

    def test_maintenance_cancellation(self):
        """Test maintenance cancellation"""
        # Schedule maintenance
        window = self.maintenance.schedule_maintenance(
            MaintenanceType.UPDATE,
            self.start_time,
            self.end_time,
            "System update",
            self.tasks,
            self.affected_services
        )
        
        # Cancel maintenance
        success = self.maintenance.cancel_maintenance(window.id)
        self.assertTrue(success)
        
        # Verify cancellation
        self.assertIsNone(
            self.maintenance.get_maintenance_status(window.id)
        )

    def test_concurrent_maintenance(self):
        """Test concurrent maintenance prevention"""
        # Schedule two maintenance windows
        window1 = self.maintenance.schedule_maintenance(
            MaintenanceType.UPDATE,
            datetime.utcnow(),
            datetime.utcnow() + timedelta(hours=1),
            "Update 1",
            self.tasks,
            self.affected_services
        )
        
        window2 = self.maintenance.schedule_maintenance(
            MaintenanceType.HOTFIX,
            datetime.utcnow(),
            datetime.utcnow() + timedelta(hours=1),
            "Update 2",
            self.tasks,
            self.affected_services
        )
        
        # Start first maintenance
        self.maintenance.start_maintenance(window1.id)
        
        # Try to start second maintenance
        success = self.maintenance.start_maintenance(window2.id)
        self.assertFalse(success)

    def test_maintenance_timeout(self):
        """Test maintenance timeout"""
        # Schedule maintenance with short window
        window = self.maintenance.schedule_maintenance(
            MaintenanceType.UPDATE,
            datetime.utcnow(),
            datetime.utcnow() + timedelta(seconds=1),
            "Quick update",
            self.tasks,  # Tasks take longer than 1 second
            self.affected_services
        )
        
        # Start maintenance
        self.maintenance.start_maintenance(window.id)
        
        # Wait for completion
        self._wait_for_maintenance()
        
        # Verify timeout
        window = self.maintenance.get_maintenance_status(window.id)
        self.assertEqual(window.state, MaintenanceState.FAILED)
        self.assertIn("exceeded", window.error.lower())

    def test_maintenance_progress(self):
        """Test maintenance progress tracking"""
        # Schedule maintenance
        window = self.maintenance.schedule_maintenance(
            MaintenanceType.UPDATE,
            datetime.utcnow(),
            datetime.utcnow() + timedelta(hours=1),
            "System update",
            self.tasks,
            self.affected_services
        )
        
        # Start maintenance
        self.maintenance.start_maintenance(window.id)
        
        # Check progress
        time.sleep(2)  # Wait for some tasks to complete
        window = self.maintenance.get_maintenance_status(window.id)
        self.assertGreater(window.progress, 0)
        self.assertLess(window.progress, 100)

    def test_emergency_maintenance(self):
        """Test emergency maintenance"""
        # Schedule emergency maintenance
        window = self.maintenance.schedule_maintenance(
            MaintenanceType.EMERGENCY,
            datetime.utcnow(),
            datetime.utcnow() + timedelta(minutes=30),
            "Emergency fix",
            [{'type': 'service_stop', 'service': 'game'},
             {'type': 'service_start', 'service': 'game'}],
            ['game']
        )
        
        # Start maintenance
        success = self.maintenance.start_maintenance(window.id)
        self.assertTrue(success)
        
        # Wait for completion
        self._wait_for_maintenance()
        
        # Verify completion
        window = self.maintenance.get_maintenance_status(window.id)
        self.assertEqual(window.state, MaintenanceState.COMPLETED)

    def _wait_for_maintenance(self, timeout: int = 10):
        """Wait for maintenance to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.maintenance.current_maintenance:
                return
            time.sleep(0.1)
        raise TimeoutError("Maintenance did not complete in time")

if __name__ == '__main__':
    unittest.main()
