import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum, auto
import time
import cProfile
import pstats
import io
import tracemalloc
import functools
import threading
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ProfilingType(Enum):
    """Types of profiling"""
    CPU = auto()
    MEMORY = auto()
    TIME = auto()
    CALLS = auto()
    IO = auto()
    DATABASE = auto()

@dataclass
class ProfilingResult:
    """Profiling result data"""
    type: ProfilingType
    timestamp: datetime
    duration: float
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ProfilingSystem:
    """System for performance profiling"""
    def __init__(self):
        self.results: Dict[str, List[ProfilingResult]] = {}
        self.active_profilers: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def profile_cpu(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, ProfilingResult]:
        """Profile CPU usage of a function"""
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        
        # Process stats
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        stats.print_stats()
        
        profiling_result = ProfilingResult(
            type=ProfilingType.CPU,
            timestamp=datetime.utcnow(),
            duration=sum(stat[3] for stat in stats.stats.values()),
            data={
                'stats': stream.getvalue(),
                'calls': stats.total_calls,
                'primitive_calls': stats.prim_calls
            }
        )
        
        return result, profiling_result

    def profile_memory(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, ProfilingResult]:
        """Profile memory usage of a function"""
        tracemalloc.start()
        start_snapshot = tracemalloc.take_snapshot()
        
        result = func(*args, **kwargs)
        
        end_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Get memory statistics
        stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        
        profiling_result = ProfilingResult(
            type=ProfilingType.MEMORY,
            timestamp=datetime.utcnow(),
            duration=0,  # Not applicable for memory profiling
            data={
                'current': tracemalloc.get_traced_memory()[0],
                'peak': tracemalloc.get_traced_memory()[1],
                'detailed_stats': [
                    {
                        'file': str(stat.traceback),
                        'size': stat.size,
                        'count': stat.count
                    }
                    for stat in stats[:10]  # Top 10 allocations
                ]
            }
        )
        
        return result, profiling_result

    def profile_time(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, ProfilingResult]:
        """Profile execution time of a function"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start_time
        
        profiling_result = ProfilingResult(
            type=ProfilingType.TIME,
            timestamp=datetime.utcnow(),
            duration=duration,
            data={
                'execution_time': duration
            }
        )
        
        return result, profiling_result

    def start_profiling(
        self,
        name: str,
        type: ProfilingType
    ):
        """Start continuous profiling"""
        with self._lock:
            if name in self.active_profilers:
                return
            
            if type == ProfilingType.CPU:
                profiler = cProfile.Profile()
                profiler.enable()
            elif type == ProfilingType.MEMORY:
                tracemalloc.start()
            
            self.active_profilers[name] = {
                'type': type,
                'start_time': datetime.utcnow(),
                'profiler': profiler if type == ProfilingType.CPU else None
            }

    def stop_profiling(self, name: str) -> Optional[ProfilingResult]:
        """Stop continuous profiling"""
        with self._lock:
            if name not in self.active_profilers:
                return None
            
            profiling = self.active_profilers.pop(name)
            type = profiling['type']
            duration = (
                datetime.utcnow() - profiling['start_time']
            ).total_seconds()
            
            if type == ProfilingType.CPU:
                profiler = profiling['profiler']
                profiler.disable()
                
                stream = io.StringIO()
                stats = pstats.Stats(profiler, stream=stream)
                stats.sort_stats('cumulative')
                stats.print_stats()
                
                data = {
                    'stats': stream.getvalue(),
                    'calls': stats.total_calls,
                    'primitive_calls': stats.prim_calls
                }
            
            elif type == ProfilingType.MEMORY:
                snapshot = tracemalloc.take_snapshot()
                tracemalloc.stop()
                
                stats = snapshot.statistics('lineno')
                data = {
                    'current': tracemalloc.get_traced_memory()[0],
                    'peak': tracemalloc.get_traced_memory()[1],
                    'detailed_stats': [
                        {
                            'file': str(stat.traceback),
                            'size': stat.size,
                            'count': stat.count
                        }
                        for stat in stats[:10]
                    ]
                }
            
            result = ProfilingResult(
                type=type,
                timestamp=profiling['start_time'],
                duration=duration,
                data=data
            )
            
            if name not in self.results:
                self.results[name] = []
            self.results[name].append(result)
            
            return result

    def get_results(
        self,
        name: Optional[str] = None,
        type: Optional[ProfilingType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List[ProfilingResult]]:
        """Get profiling results with filtering"""
        results = {}
        
        for profile_name, profile_results in self.results.items():
            if name and profile_name != name:
                continue
            
            filtered_results = []
            for result in profile_results:
                if type and result.type != type:
                    continue
                
                if start_time and result.timestamp < start_time:
                    continue
                
                if end_time and result.timestamp > end_time:
                    continue
                
                filtered_results.append(result)
            
            if filtered_results:
                results[profile_name] = filtered_results
        
        return results

class TestProfiling(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.profiling = ProfilingSystem()

    def test_cpu_profiling(self):
        """Test CPU profiling"""
        def cpu_intensive_task():
            """CPU intensive task for testing"""
            result = 0
            for i in range(1000000):
                result += i
            return result
        
        # Profile function
        result, profile = self.profiling.profile_cpu(cpu_intensive_task)
        
        # Verify profiling
        self.assertEqual(profile.type, ProfilingType.CPU)
        self.assertGreater(profile.duration, 0)
        self.assertIn('stats', profile.data)
        self.assertGreater(profile.data['calls'], 0)

    def test_memory_profiling(self):
        """Test memory profiling"""
        def memory_intensive_task():
            """Memory intensive task for testing"""
            return [i for i in range(1000000)]
        
        # Profile function
        result, profile = self.profiling.profile_memory(memory_intensive_task)
        
        # Verify profiling
        self.assertEqual(profile.type, ProfilingType.MEMORY)
        self.assertGreater(profile.data['current'], 0)
        self.assertGreater(profile.data['peak'], 0)
        self.assertGreater(len(profile.data['detailed_stats']), 0)

    def test_time_profiling(self):
        """Test time profiling"""
        def time_intensive_task():
            """Time intensive task for testing"""
            time.sleep(0.1)
            return True
        
        # Profile function
        result, profile = self.profiling.profile_time(time_intensive_task)
        
        # Verify profiling
        self.assertEqual(profile.type, ProfilingType.TIME)
        self.assertGreater(profile.duration, 0.1)
        self.assertGreater(profile.data['execution_time'], 0.1)

    def test_continuous_profiling(self):
        """Test continuous profiling"""
        # Start CPU profiling
        self.profiling.start_profiling("test_profile", ProfilingType.CPU)
        
        # Perform some work
        result = 0
        for i in range(100000):
            result += i
        
        # Stop profiling
        profile = self.profiling.stop_profiling("test_profile")
        
        # Verify profiling
        self.assertIsNotNone(profile)
        self.assertEqual(profile.type, ProfilingType.CPU)
        self.assertGreater(profile.duration, 0)

    def test_result_filtering(self):
        """Test profiling result filtering"""
        def test_task():
            time.sleep(0.1)
        
        # Create multiple profiles
        for i in range(3):
            result, profile = self.profiling.profile_time(test_task)
            if "test" not in self.profiling.results:
                self.profiling.results["test"] = []
            self.profiling.results["test"].append(profile)
        
        # Filter results
        results = self.profiling.get_results(
            name="test",
            type=ProfilingType.TIME
        )
        
        # Verify filtering
        self.assertEqual(len(results["test"]), 3)
        for profile in results["test"]:
            self.assertEqual(profile.type, ProfilingType.TIME)

    def test_multiple_profilers(self):
        """Test multiple simultaneous profilers"""
        # Start multiple profilers
        self.profiling.start_profiling("cpu_profile", ProfilingType.CPU)
        self.profiling.start_profiling("memory_profile", ProfilingType.MEMORY)
        
        # Perform some work
        data = [i for i in range(100000)]
        
        # Stop profilers
        cpu_profile = self.profiling.stop_profiling("cpu_profile")
        memory_profile = self.profiling.stop_profiling("memory_profile")
        
        # Verify both profiles
        self.assertIsNotNone(cpu_profile)
        self.assertIsNotNone(memory_profile)
        self.assertEqual(cpu_profile.type, ProfilingType.CPU)
        self.assertEqual(memory_profile.type, ProfilingType.MEMORY)

    def test_profiling_decorator(self):
        """Test profiling decorator"""
        def profile_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result, profile = self.profiling.profile_time(
                    func,
                    *args,
                    **kwargs
                )
                return result
            return wrapper
        
        @profile_decorator
        def test_function():
            time.sleep(0.1)
            return True
        
        # Call decorated function
        result = test_function()
        
        # Verify profiling
        self.assertTrue(result)
        self.assertEqual(len(self.profiling.results), 0)  # Results not stored

    def test_error_handling(self):
        """Test profiling error handling"""
        def error_function():
            raise ValueError("Test error")
        
        # Profile function that raises error
        with self.assertRaises(ValueError):
            result, profile = self.profiling.profile_time(error_function)
        
        # Try to stop non-existent profile
        result = self.profiling.stop_profiling("nonexistent")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
