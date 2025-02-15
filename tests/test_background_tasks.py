import unittest
from unittest.mock import Mock, patch
import sys
import os
import asyncio
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import User, Gate, Guild

class TaskQueue:
    """Task queue for background processing"""
    def __init__(self):
        self.queue = queue.PriorityQueue()
        self.running = False
        self.workers: List[threading.Thread] = []

    def enqueue(self, task: 'Task', priority: int = 0):
        """Add task to queue"""
        self.queue.put((priority, task))

    def start_workers(self, num_workers: int = 4):
        """Start worker threads"""
        self.running = True
        for _ in range(num_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop_workers(self):
        """Stop worker threads"""
        self.running = False
        for _ in self.workers:
            self.queue.put((0, None))  # Signal workers to stop
        for worker in self.workers:
            worker.join()
        self.workers.clear()

    def _worker_loop(self):
        """Worker thread main loop"""
        while self.running:
            try:
                priority, task = self.queue.get(timeout=1)
                if task is None:
                    break
                task.execute()
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing task: {e}")

class Task:
    """Base class for background tasks"""
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.error = None
        self.completed = False
        self.created_at = datetime.utcnow()

    def execute(self):
        """Execute the task"""
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.completed = True
        except Exception as e:
            self.error = e
            raise

class ScheduledTask(Task):
    """Task scheduled for future execution"""
    def __init__(self, func: Callable, scheduled_time: datetime, *args, **kwargs):
        super().__init__(func, *args, **kwargs)
        self.scheduled_time = scheduled_time

    def is_due(self) -> bool:
        """Check if task is due for execution"""
        return datetime.utcnow() >= self.scheduled_time

class RecurringTask(Task):
    """Task that recurs at regular intervals"""
    def __init__(self, func: Callable, interval: timedelta, *args, **kwargs):
        super().__init__(func, *args, **kwargs)
        self.interval = interval
        self.last_run = None

    def is_due(self) -> bool:
        """Check if task is due for execution"""
        if self.last_run is None:
            return True
        return datetime.utcnow() >= self.last_run + self.interval

    def execute(self):
        """Execute the task and update last run time"""
        super().execute()
        self.last_run = datetime.utcnow()

class TestBackgroundTasks(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.task_queue = TaskQueue()
        self.task_queue.start_workers()

    def tearDown(self):
        """Clean up after each test"""
        self.task_queue.stop_workers()

    def test_basic_task_execution(self):
        """Test basic task execution"""
        result = []
        
        def test_task():
            result.append(1)
        
        # Create and enqueue task
        task = Task(test_task)
        self.task_queue.enqueue(task)
        
        # Wait for task completion
        time.sleep(0.1)
        
        self.assertEqual(result, [1])
        self.assertTrue(task.completed)
        self.assertIsNone(task.error)

    def test_task_priorities(self):
        """Test task priority handling"""
        results = []
        
        def task_with_id(task_id: int):
            results.append(task_id)
        
        # Create tasks with different priorities
        tasks = [
            (Task(task_with_id, 1), 2),  # Lower priority
            (Task(task_with_id, 2), 1),  # Higher priority
            (Task(task_with_id, 3), 1)   # Same high priority
        ]
        
        # Enqueue tasks
        for task, priority in tasks:
            self.task_queue.enqueue(task, priority)
        
        # Wait for task completion
        time.sleep(0.1)
        
        # Higher priority tasks should be executed first
        self.assertEqual(results[0], 2)  # Higher priority
        self.assertEqual(results[1], 3)  # Same high priority
        self.assertEqual(results[2], 1)  # Lower priority

    def test_scheduled_tasks(self):
        """Test scheduled task execution"""
        result = []
        
        def scheduled_task():
            result.append(datetime.utcnow())
        
        # Schedule task for future execution
        scheduled_time = datetime.utcnow() + timedelta(seconds=1)
        task = ScheduledTask(scheduled_task, scheduled_time)
        
        # Task shouldn't execute immediately
        self.assertFalse(task.is_due())
        
        # Wait until scheduled time
        time.sleep(1.1)
        
        # Task should be due now
        self.assertTrue(task.is_due())
        task.execute()
        
        self.assertEqual(len(result), 1)
        self.assertGreaterEqual(result[0], scheduled_time)

    def test_recurring_tasks(self):
        """Test recurring task execution"""
        executions = []
        
        def recurring_task():
            executions.append(datetime.utcnow())
        
        # Create recurring task
        task = RecurringTask(recurring_task, timedelta(seconds=1))
        
        # Execute multiple times
        for _ in range(3):
            if task.is_due():
                task.execute()
            time.sleep(1)
        
        self.assertEqual(len(executions), 3)
        for i in range(1, len(executions)):
            time_diff = executions[i] - executions[i-1]
            self.assertGreaterEqual(time_diff.total_seconds(), 1)

    def test_error_handling(self):
        """Test task error handling"""
        def failing_task():
            raise ValueError("Task error")
        
        # Create task that will fail
        task = Task(failing_task)
        self.task_queue.enqueue(task)
        
        # Wait for task execution
        time.sleep(0.1)
        
        self.assertIsInstance(task.error, ValueError)
        self.assertFalse(task.completed)

    def test_async_tasks(self):
        """Test asynchronous task execution"""
        async def async_task():
            await asyncio.sleep(0.1)
            return "async result"
        
        # Create async task wrapper
        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(async_task())
        
        # Execute async task
        task = Task(run_async_task)
        self.task_queue.enqueue(task)
        
        # Wait for completion
        time.sleep(0.2)
        
        self.assertEqual(task.result, "async result")
        self.assertTrue(task.completed)

    def test_task_chaining(self):
        """Test chaining multiple tasks"""
        results = []
        
        def task1():
            results.append(1)
            return "task1 result"
        
        def task2(prev_result):
            results.append(2)
            return f"{prev_result} -> task2"
        
        # Create and chain tasks
        task1_obj = Task(task1)
        task2_obj = Task(task2, "task1 result")
        
        self.task_queue.enqueue(task1_obj)
        self.task_queue.enqueue(task2_obj)
        
        # Wait for completion
        time.sleep(0.1)
        
        self.assertEqual(results, [1, 2])
        self.assertEqual(task2_obj.result, "task1 result -> task2")

    def test_task_batching(self):
        """Test task batching"""
        results = []
        
        def batch_task(items):
            results.extend(items)
        
        # Create batch of tasks
        batch_size = 5
        items = list(range(batch_size))
        
        task = Task(batch_task, items)
        self.task_queue.enqueue(task)
        
        # Wait for completion
        time.sleep(0.1)
        
        self.assertEqual(len(results), batch_size)
        self.assertEqual(results, items)

    def test_task_cancellation(self):
        """Test task cancellation"""
        def long_running_task():
            time.sleep(5)
            return "completed"
        
        # Start task
        task = Task(long_running_task)
        self.task_queue.enqueue(task)
        
        # Stop workers (simulating cancellation)
        time.sleep(0.1)
        self.task_queue.stop_workers()
        
        self.assertFalse(task.completed)

    def test_task_monitoring(self):
        """Test task monitoring capabilities"""
        def monitored_task():
            time.sleep(0.1)
        
        # Create task with monitoring
        start_time = datetime.utcnow()
        task = Task(monitored_task)
        self.task_queue.enqueue(task)
        
        # Wait for completion
        time.sleep(0.2)
        
        # Verify monitoring data
        self.assertTrue(task.completed)
        self.assertGreaterEqual(
            datetime.utcnow() - task.created_at,
            timedelta(seconds=0.1)
        )

if __name__ == '__main__':
    unittest.main()
