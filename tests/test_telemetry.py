import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import json
import queue
import threading
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TelemetryType(Enum):
    """Types of telemetry data"""
    PERFORMANCE = auto()
    GAMEPLAY = auto()
    NETWORK = auto()
    ERROR = auto()
    DIAGNOSTIC = auto()
    USAGE = auto()

@dataclass
class TelemetryEvent:
    """Telemetry event data"""
    id: str
    type: TelemetryType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class TelemetrySystem:
    """System for game telemetry"""
    def __init__(self, storage_dir: str = 'telemetry'):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.event_queue = queue.Queue()
        self.batch_size = 100
        self.flush_interval = 60  # seconds
        self.events: Dict[TelemetryType, List[TelemetryEvent]] = {}
        self.running = False
        self._worker_thread = None
        self._flush_thread = None
        self._lock = threading.Lock()
        self.start()

    def start(self):
        """Start telemetry system"""
        self.running = True
        self._worker_thread = threading.Thread(
            target=self._process_events
        )
        self._worker_thread.daemon = True
        self._worker_thread.start()
        
        self._flush_thread = threading.Thread(
            target=self._periodic_flush
        )
        self._flush_thread.daemon = True
        self._flush_thread.start()

    def stop(self):
        """Stop telemetry system"""
        self.running = False
        if self._worker_thread:
            self._worker_thread.join()
        if self._flush_thread:
            self._flush_thread.join()
        self.flush()

    def track(
        self,
        type: TelemetryType,
        source: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """Track telemetry event"""
        event = TelemetryEvent(
            id=f"evt_{int(time.time()*1000)}",
            type=type,
            timestamp=datetime.utcnow(),
            source=source,
            data=data,
            context=context,
            session_id=session_id
        )
        
        self.event_queue.put(event)

    def get_events(
        self,
        type: Optional[TelemetryType] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> List[TelemetryEvent]:
        """Get telemetry events with filtering"""
        events = []
        
        for event_type, type_events in self.events.items():
            if type and event_type != type:
                continue
            
            for event in type_events:
                if source and event.source != source:
                    continue
                
                if start_time and event.timestamp < start_time:
                    continue
                
                if end_time and event.timestamp > end_time:
                    continue
                
                if session_id and event.session_id != session_id:
                    continue
                
                events.append(event)
        
        return sorted(events, key=lambda e: e.timestamp)

    def get_session_events(
        self,
        session_id: str
    ) -> List[TelemetryEvent]:
        """Get all events for a session"""
        return self.get_events(session_id=session_id)

    def flush(self):
        """Flush events to storage"""
        with self._lock:
            for type, events in self.events.items():
                if not events:
                    continue
                
                file_path = os.path.join(
                    self.storage_dir,
                    f"{type.name.lower()}_{datetime.utcnow().date()}.json"
                )
                
                data = [
                    {
                        'id': e.id,
                        'timestamp': e.timestamp.isoformat(),
                        'source': e.source,
                        'data': e.data,
                        'context': e.context,
                        'session_id': e.session_id
                    }
                    for e in events
                ]
                
                with open(file_path, 'a') as f:
                    for event in data:
                        f.write(json.dumps(event) + '\n')
                
                events.clear()

    def _process_events(self):
        """Process events from queue"""
        batch = []
        
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                batch.append(event)
                
                # Process batch if full
                if len(batch) >= self.batch_size:
                    self._store_batch(batch)
                    batch = []
                
            except queue.Empty:
                if batch:
                    self._store_batch(batch)
                    batch = []

    def _store_batch(self, batch: List[TelemetryEvent]):
        """Store batch of events"""
        with self._lock:
            for event in batch:
                if event.type not in self.events:
                    self.events[event.type] = []
                self.events[event.type].append(event)

    def _periodic_flush(self):
        """Periodically flush events to storage"""
        while self.running:
            time.sleep(self.flush_interval)
            self.flush()

class TestTelemetry(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.telemetry = TelemetrySystem('test_telemetry')

    def tearDown(self):
        """Clean up after each test"""
        self.telemetry.stop()
        import shutil
        if os.path.exists('test_telemetry'):
            shutil.rmtree('test_telemetry')

    def test_basic_tracking(self):
        """Test basic telemetry tracking"""
        # Track event
        self.telemetry.track(
            TelemetryType.PERFORMANCE,
            'game_client',
            {'fps': 60, 'memory_usage': 1024}
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Get events
        events = self.telemetry.get_events(
            type=TelemetryType.PERFORMANCE
        )
        
        # Verify event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].source, 'game_client')
        self.assertEqual(events[0].data['fps'], 60)

    def test_session_tracking(self):
        """Test session-based tracking"""
        session_id = 'test_session'
        
        # Track session events
        self.telemetry.track(
            TelemetryType.GAMEPLAY,
            'game_client',
            {'action': 'login'},
            session_id=session_id
        )
        
        self.telemetry.track(
            TelemetryType.GAMEPLAY,
            'game_client',
            {'action': 'logout'},
            session_id=session_id
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Get session events
        events = self.telemetry.get_session_events(session_id)
        
        # Verify events
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].data['action'], 'login')
        self.assertEqual(events[1].data['action'], 'logout')

    def test_event_filtering(self):
        """Test event filtering"""
        # Track events from different sources
        sources = ['client', 'server']
        for source in sources:
            self.telemetry.track(
                TelemetryType.NETWORK,
                source,
                {'latency': 50}
            )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Filter by source
        events = self.telemetry.get_events(source='client')
        
        # Verify filtering
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].source, 'client')

    def test_batch_processing(self):
        """Test batch event processing"""
        # Track many events
        for i in range(150):  # More than batch size
            self.telemetry.track(
                TelemetryType.USAGE,
                'test',
                {'count': i}
            )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Get events
        events = self.telemetry.get_events(
            type=TelemetryType.USAGE
        )
        
        # Verify batch processing
        self.assertEqual(len(events), 150)

    def test_periodic_flush(self):
        """Test periodic event flushing"""
        # Reduce flush interval for testing
        self.telemetry.flush_interval = 1
        
        # Track event
        self.telemetry.track(
            TelemetryType.DIAGNOSTIC,
            'test',
            {'status': 'ok'}
        )
        
        # Wait for flush
        time.sleep(1.1)
        
        # Verify file creation
        files = os.listdir('test_telemetry')
        self.assertGreater(len(files), 0)
        self.assertTrue(
            any(f.startswith('diagnostic_') for f in files)
        )

    def test_context_data(self):
        """Test context data handling"""
        context = {
            'client_version': '1.0.0',
            'platform': 'windows'
        }
        
        # Track with context
        self.telemetry.track(
            TelemetryType.ERROR,
            'test',
            {'error': 'test_error'},
            context=context
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Get events
        events = self.telemetry.get_events(
            type=TelemetryType.ERROR
        )
        
        # Verify context
        self.assertEqual(
            events[0].context['client_version'],
            '1.0.0'
        )

    def test_time_filtering(self):
        """Test time-based filtering"""
        now = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's event
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            self.telemetry.track(
                TelemetryType.USAGE,
                'test',
                {'old': True}
            )
            
            # Today's event
            mock_datetime.utcnow.return_value = now
            self.telemetry.track(
                TelemetryType.USAGE,
                'test',
                {'new': True}
            )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Get recent events
        events = self.telemetry.get_events(
            start_time=now - timedelta(hours=1)
        )
        
        # Verify filtering
        self.assertEqual(len(events), 1)
        self.assertIn('new', events[0].data)

    def test_error_handling(self):
        """Test error event handling"""
        # Track error event
        error_data = {
            'type': 'RuntimeError',
            'message': 'Test error',
            'stack_trace': 'test_file.py:123'
        }
        
        self.telemetry.track(
            TelemetryType.ERROR,
            'test',
            error_data
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Get error events
        events = self.telemetry.get_events(
            type=TelemetryType.ERROR
        )
        
        # Verify error data
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0].data['type'],
            'RuntimeError'
        )

if __name__ == '__main__':
    unittest.main()
