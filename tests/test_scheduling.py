import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum, auto
import asyncio
import time
import heapq
import threading

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()

class TaskStatus(Enum):
    """Task status states"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class ScheduledTask:
    """Scheduled task data"""
    id: int
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    execute_at: datetime
    repeat_interval: Optional[timedelta] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None

class SchedulingSystem:
    """Task scheduling system"""
    def __init__(self):
        self.tasks: Dict[int, ScheduledTask] = {}
        self.task_queue = []  # Priority queue
        self.next_task_id = 1
        self.running = False
        self.lock = threading.Lock()
        self._schedule_thread = None

    def schedule_task(
        self,
        name: str,
        func: Callable,
        execute_at: datetime,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        repeat_interval: Optional[timedelta] = None
    ) -> int:
        """Schedule a new task"""
        with self.lock:
            task = ScheduledTask(
                id=self.next_task_id,
                name=name,
                func=func,
                args=args,
                kwargs=kwargs or {},
                priority=priority,
                execute_at=execute_at,
                repeat_interval=repeat_interval,
                next_run=execute_at
            )
            
            self.tasks[task.id] = task
            heapq.heappush(
                self.task_queue,
                (execute_at, priority.value, task.id)
            )
            
            self.next_task_id += 1
            return task.id

    def cancel_task(self, task_id: int) -> bool:
        """Cancel a scheduled task"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                return False
            
            task.status = TaskStatus.CANCELLED
            return True

    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> List[ScheduledTask]:
        """Get all pending tasks"""
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
        ]

    def start(self):
        """Start the scheduling system"""
        if self._schedule_thread is not None:
            return
        
        self.running = True
        self._schedule_thread = threading.Thread(
            target=self._run_scheduler
        )
        self._schedule_thread.daemon = True
        self._schedule_thread.start()

    def stop(self):
        """Stop the scheduling system"""
        self.running = False
        if self._schedule_thread:
            self._schedule_thread.join()
            self._schedule_thread = None

    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            now = datetime.utcnow()
            
            with self.lock:
                while self.task_queue:
                    execute_at, _, task_id = self.task_queue[0]
                    
                    if execute_at > now:
                        break
                    
                    heapq.heappop(self.task_queue)
                    task = self.tasks[task_id]
                    
                    if task.status != TaskStatus.PENDING:
                        continue
                    
                    self._execute_task(task)
                    
                    # Reschedule if recurring
                    if task.repeat_interval:
                        next_run = task.next_run + task.repeat_interval
                        task.last_run = task.next_run
                        task.next_run = next_run
                        task.status = TaskStatus.PENDING
                        
                        heapq.heappush(
                            self.task_queue,
                            (next_run, task.priority.value, task.id)
                        )
            
            time.sleep(0.1)  # Prevent busy waiting

    def _execute_task(self, task: ScheduledTask):
        """Execute a task"""
        task.status = TaskStatus.RUNNING
        
        try:
            task.func(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

class TestScheduling(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.scheduler = SchedulingSystem()
        self.scheduler.start()
        self.results = []

    def tearDown(self):
        """Clean up after each test"""
        self.scheduler.stop()

    def test_basic_scheduling(self):
        """Test basic task scheduling"""
        def test_task():
            self.results.append(datetime.utcnow())
        
        # Schedule task
        execute_at = datetime.utcnow() + timedelta(seconds=1)
        task_id = self.scheduler.schedule_task(
            "test_task",
            test_task,
            execute_at
        )
        
        # Wait for execution
        time.sleep(1.5)
        
        # Verify execution
        self.assertEqual(len(self.results), 1)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_recurring_tasks(self):
        """Test recurring task scheduling"""
        def recurring_task():
            self.results.append(datetime.utcnow())
        
        # Schedule recurring task
        execute_at = datetime.utcnow() + timedelta(seconds=1)
        self.scheduler.schedule_task(
            "recurring_task",
            recurring_task,
            execute_at,
            repeat_interval=timedelta(seconds=1)
        )
        
        # Wait for multiple executions
        time.sleep(3.5)
        
        # Verify multiple executions
        self.assertGreaterEqual(len(self.results), 3)

    def test_task_priorities(self):
        """Test task priority handling"""
        execution_order = []
        
        def priority_task(priority: str):
            execution_order.append(priority)
        
        # Schedule tasks with different priorities
        now = datetime.utcnow()
        self.scheduler.schedule_task(
            "low_priority",
            priority_task,
            now + timedelta(seconds=1),
            args=("low",),
            priority=TaskPriority.LOW
        )
        self.scheduler.schedule_task(
            "high_priority",
            priority_task,
            now + timedelta(seconds=1),
            args=("high",),
            priority=TaskPriority.HIGH
        )
        
        # Wait for execution
        time.sleep(1.5)
        
        # Verify execution order
        self.assertEqual(execution_order[0], "high")
        self.assertEqual(execution_order[1], "low")

    def test_task_cancellation(self):
        """Test task cancellation"""
        def cancelled_task():
            self.results.append("executed")
        
        # Schedule and cancel task
        task_id = self.scheduler.schedule_task(
            "cancelled_task",
            cancelled_task,
            datetime.utcnow() + timedelta(seconds=1)
        )
        
        success = self.scheduler.cancel_task(task_id)
        
        # Verify cancellation
        self.assertTrue(success)
        time.sleep(1.5)
        self.assertEqual(len(self.results), 0)
        
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.CANCELLED)

    def test_error_handling(self):
        """Test error handling in tasks"""
        def failing_task():
            raise ValueError("Test error")
        
        # Schedule failing task
        task_id = self.scheduler.schedule_task(
            "failing_task",
            failing_task,
            datetime.utcnow() + timedelta(seconds=1)
        )
        
        # Wait for execution
        time.sleep(1.5)
        
        # Verify error handling
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIn("Test error", task.error)

    def test_concurrent_tasks(self):
        """Test concurrent task execution"""
        def slow_task(task_id: str):
            time.sleep(1)
            self.results.append(task_id)
        
        # Schedule multiple tasks
        now = datetime.utcnow()
        for i in range(3):
            self.scheduler.schedule_task(
                f"task_{i}",
                slow_task,
                now + timedelta(seconds=1),
                args=(f"task_{i}",)
            )
        
        # Wait for execution
        time.sleep(2.5)
        
        # Verify all tasks completed
        self.assertEqual(len(self.results), 3)

    def test_task_query(self):
        """Test task querying"""
        # Schedule multiple tasks
        now = datetime.utcnow()
        task_ids = []
        for i in range(3):
            task_id = self.scheduler.schedule_task(
                f"task_{i}",
                lambda: None,
                now + timedelta(seconds=i+1)
            )
            task_ids.append(task_id)
        
        # Query pending tasks
        pending = self.scheduler.get_pending_tasks()
        self.assertEqual(len(pending), 3)
        
        # Wait and verify completion
        time.sleep(4)
        pending = self.scheduler.get_pending_tasks()
        self.assertEqual(len(pending), 0)

    def test_scheduler_restart(self):
        """Test scheduler stop/start functionality"""
        def restart_task():
            self.results.append(datetime.utcnow())
        
        # Schedule task
        self.scheduler.schedule_task(
            "restart_task",
            restart_task,
            datetime.utcnow() + timedelta(seconds=2)
        )
        
        # Stop and restart scheduler
        self.scheduler.stop()
        time.sleep(0.5)
        self.scheduler.start()
        
        # Wait for execution
        time.sleep(2)
        
        # Verify task executed
        self.assertEqual(len(self.results), 1)

    def test_long_running_tasks(self):
        """Test handling of long-running tasks"""
        def long_task():
            time.sleep(2)
            self.results.append(datetime.utcnow())
        
        # Schedule long task
        task_id = self.scheduler.schedule_task(
            "long_task",
            long_task,
            datetime.utcnow() + timedelta(seconds=1)
        )
        
        # Check status during execution
        time.sleep(1.5)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.RUNNING)
        
        # Wait for completion
        time.sleep(2)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_task_dependencies(self):
        """Test task dependencies"""
        def dependent_task(dependency_result):
            self.results.append(dependency_result * 2)
        
        def main_task():
            result = 42
            self.results.append(result)
            return result
        
        # Schedule dependent tasks
        now = datetime.utcnow()
        main_task_id = self.scheduler.schedule_task(
            "main_task",
            main_task,
            now + timedelta(seconds=1)
        )
        
        self.scheduler.schedule_task(
            "dependent_task",
            dependent_task,
            now + timedelta(seconds=2),
            args=(42,)
        )
        
        # Wait for execution
        time.sleep(2.5)
        
        # Verify execution order and results
        self.assertEqual(self.results[0], 42)
        self.assertEqual(self.results[1], 84)

if __name__ == '__main__':
    unittest.main()
