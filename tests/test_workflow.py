import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum, auto
import asyncio
import json
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WorkflowState(Enum):
    """Workflow states"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    PAUSED = auto()

class StepResult(Enum):
    """Step execution results"""
    SUCCESS = auto()
    FAILURE = auto()
    RETRY = auto()
    SKIP = auto()

@dataclass
class WorkflowStep:
    """Workflow step data"""
    id: str
    name: str
    action: Callable
    dependencies: List[str]
    retry_count: int = 3
    timeout: int = 60  # seconds
    required: bool = True
    data: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowInstance:
    """Workflow instance data"""
    id: str
    workflow_id: str
    state: WorkflowState
    context: Dict[str, Any]
    steps: Dict[str, WorkflowStep]
    results: Dict[str, StepResult]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class WorkflowSystem:
    """System for workflow management"""
    def __init__(self):
        self.workflows: Dict[str, Dict[str, WorkflowStep]] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.running_instances: Dict[str, asyncio.Task] = {}

    def register_workflow(
        self,
        workflow_id: str,
        steps: List[WorkflowStep]
    ):
        """Register a workflow"""
        self.workflows[workflow_id] = {
            step.id: step for step in steps
        }

    async def start_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """Start a workflow instance"""
        if workflow_id not in self.workflows:
            return None
        
        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            id=instance_id,
            workflow_id=workflow_id,
            state=WorkflowState.PENDING,
            context=context or {},
            steps=self.workflows[workflow_id].copy(),
            results={},
            started_at=datetime.utcnow()
        )
        
        self.instances[instance_id] = instance
        
        # Start execution
        task = asyncio.create_task(
            self._execute_workflow(instance)
        )
        self.running_instances[instance_id] = task
        
        return instance_id

    async def cancel_workflow(self, instance_id: str) -> bool:
        """Cancel a workflow instance"""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        if instance.state not in (
            WorkflowState.PENDING,
            WorkflowState.RUNNING
        ):
            return False
        
        if instance_id in self.running_instances:
            self.running_instances[instance_id].cancel()
            del self.running_instances[instance_id]
        
        instance.state = WorkflowState.CANCELLED
        instance.completed_at = datetime.utcnow()
        return True

    async def pause_workflow(self, instance_id: str) -> bool:
        """Pause a workflow instance"""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        if instance.state != WorkflowState.RUNNING:
            return False
        
        instance.state = WorkflowState.PAUSED
        return True

    async def resume_workflow(self, instance_id: str) -> bool:
        """Resume a paused workflow"""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        if instance.state != WorkflowState.PAUSED:
            return False
        
        instance.state = WorkflowState.RUNNING
        
        # Resume execution
        task = asyncio.create_task(
            self._execute_workflow(instance)
        )
        self.running_instances[instance_id] = task
        
        return True

    def get_instance(
        self,
        instance_id: str
    ) -> Optional[WorkflowInstance]:
        """Get workflow instance"""
        return self.instances.get(instance_id)

    def get_step_result(
        self,
        instance_id: str,
        step_id: str
    ) -> Optional[StepResult]:
        """Get step execution result"""
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        return instance.results.get(step_id)

    async def _execute_workflow(self, instance: WorkflowInstance):
        """Execute workflow instance"""
        try:
            instance.state = WorkflowState.RUNNING
            steps = self._get_execution_order(instance.steps)
            
            for step in steps:
                if instance.state != WorkflowState.RUNNING:
                    break
                
                # Check dependencies
                if not self._check_dependencies(step, instance):
                    if step.required:
                        raise Exception(
                            f"Dependencies failed for step {step.id}"
                        )
                    instance.results[step.id] = StepResult.SKIP
                    continue
                
                # Execute step
                result = await self._execute_step(step, instance)
                instance.results[step.id] = result
                
                if result == StepResult.FAILURE and step.required:
                    raise Exception(f"Step {step.id} failed")
            
            instance.state = WorkflowState.COMPLETED
            
        except Exception as e:
            instance.state = WorkflowState.FAILED
            instance.error = str(e)
        
        finally:
            instance.completed_at = datetime.utcnow()
            if instance.id in self.running_instances:
                del self.running_instances[instance.id]

    def _get_execution_order(
        self,
        steps: Dict[str, WorkflowStep]
    ) -> List[WorkflowStep]:
        """Get step execution order"""
        ordered = []
        visited = set()
        
        def visit(step_id):
            if step_id in visited:
                return
            visited.add(step_id)
            
            step = steps[step_id]
            for dep in step.dependencies:
                visit(dep)
            ordered.append(step)
        
        for step_id in steps:
            visit(step_id)
        
        return ordered

    def _check_dependencies(
        self,
        step: WorkflowStep,
        instance: WorkflowInstance
    ) -> bool:
        """Check step dependencies"""
        for dep_id in step.dependencies:
            if dep_id not in instance.results:
                return False
            if instance.results[dep_id] != StepResult.SUCCESS:
                return False
        return True

    async def _execute_step(
        self,
        step: WorkflowStep,
        instance: WorkflowInstance
    ) -> StepResult:
        """Execute workflow step"""
        for attempt in range(step.retry_count):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    step.action(instance.context),
                    timeout=step.timeout
                )
                
                return StepResult.SUCCESS if result else StepResult.FAILURE
                
            except asyncio.TimeoutError:
                continue
            except Exception:
                if attempt < step.retry_count - 1:
                    continue
                return StepResult.FAILURE
        
        return StepResult.FAILURE

class TestWorkflow(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.workflow = WorkflowSystem()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after each test"""
        self.loop.close()

    def test_workflow_registration(self):
        """Test workflow registration"""
        async def step1(context):
            return True
        
        async def step2(context):
            return True
        
        # Create workflow steps
        steps = [
            WorkflowStep(
                id="step1",
                name="Step 1",
                action=step1,
                dependencies=[]
            ),
            WorkflowStep(
                id="step2",
                name="Step 2",
                action=step2,
                dependencies=["step1"]
            )
        ]
        
        # Register workflow
        self.workflow.register_workflow("test_flow", steps)
        
        # Verify registration
        self.assertIn("test_flow", self.workflow.workflows)
        self.assertEqual(
            len(self.workflow.workflows["test_flow"]),
            2
        )

    def test_workflow_execution(self):
        """Test workflow execution"""
        results = []
        
        async def step1(context):
            results.append(1)
            return True
        
        async def step2(context):
            results.append(2)
            return True
        
        # Create workflow
        steps = [
            WorkflowStep(
                id="step1",
                name="Step 1",
                action=step1,
                dependencies=[]
            ),
            WorkflowStep(
                id="step2",
                name="Step 2",
                action=step2,
                dependencies=["step1"]
            )
        ]
        
        self.workflow.register_workflow("test_flow", steps)
        
        # Execute workflow
        instance_id = self.loop.run_until_complete(
            self.workflow.start_workflow("test_flow")
        )
        
        # Wait for completion
        while True:
            instance = self.workflow.get_instance(instance_id)
            if instance.state in (
                WorkflowState.COMPLETED,
                WorkflowState.FAILED
            ):
                break
            self.loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify execution
        self.assertEqual(results, [1, 2])
        self.assertEqual(instance.state, WorkflowState.COMPLETED)

    def test_workflow_cancellation(self):
        """Test workflow cancellation"""
        async def long_step(context):
            await asyncio.sleep(10)
            return True
        
        # Create workflow
        steps = [
            WorkflowStep(
                id="long_step",
                name="Long Step",
                action=long_step,
                dependencies=[]
            )
        ]
        
        self.workflow.register_workflow("test_flow", steps)
        
        # Start workflow
        instance_id = self.loop.run_until_complete(
            self.workflow.start_workflow("test_flow")
        )
        
        # Cancel workflow
        success = self.loop.run_until_complete(
            self.workflow.cancel_workflow(instance_id)
        )
        
        # Verify cancellation
        self.assertTrue(success)
        instance = self.workflow.get_instance(instance_id)
        self.assertEqual(instance.state, WorkflowState.CANCELLED)

    def test_step_dependencies(self):
        """Test step dependency handling"""
        results = []
        
        async def step1(context):
            results.append(1)
            return False  # Fail this step
        
        async def step2(context):
            results.append(2)
            return True
        
        # Create workflow
        steps = [
            WorkflowStep(
                id="step1",
                name="Step 1",
                action=step1,
                dependencies=[]
            ),
            WorkflowStep(
                id="step2",
                name="Step 2",
                action=step2,
                dependencies=["step1"]
            )
        ]
        
        self.workflow.register_workflow("test_flow", steps)
        
        # Execute workflow
        instance_id = self.loop.run_until_complete(
            self.workflow.start_workflow("test_flow")
        )
        
        # Wait for completion
        while True:
            instance = self.workflow.get_instance(instance_id)
            if instance.state in (
                WorkflowState.COMPLETED,
                WorkflowState.FAILED
            ):
                break
            self.loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify dependency handling
        self.assertEqual(results, [1])  # Step 2 should not execute
        self.assertEqual(instance.state, WorkflowState.FAILED)

    def test_step_retries(self):
        """Test step retry mechanism"""
        attempts = 0
        
        async def failing_step(context):
            nonlocal attempts
            attempts += 1
            return False
        
        # Create workflow
        steps = [
            WorkflowStep(
                id="failing_step",
                name="Failing Step",
                action=failing_step,
                dependencies=[],
                retry_count=3
            )
        ]
        
        self.workflow.register_workflow("test_flow", steps)
        
        # Execute workflow
        instance_id = self.loop.run_until_complete(
            self.workflow.start_workflow("test_flow")
        )
        
        # Wait for completion
        while True:
            instance = self.workflow.get_instance(instance_id)
            if instance.state in (
                WorkflowState.COMPLETED,
                WorkflowState.FAILED
            ):
                break
            self.loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify retries
        self.assertEqual(attempts, 3)
        self.assertEqual(instance.state, WorkflowState.FAILED)

    def test_workflow_context(self):
        """Test workflow context sharing"""
        async def step1(context):
            context['value'] = 42
            return True
        
        async def step2(context):
            return context.get('value') == 42
        
        # Create workflow
        steps = [
            WorkflowStep(
                id="step1",
                name="Step 1",
                action=step1,
                dependencies=[]
            ),
            WorkflowStep(
                id="step2",
                name="Step 2",
                action=step2,
                dependencies=["step1"]
            )
        ]
        
        self.workflow.register_workflow("test_flow", steps)
        
        # Execute workflow
        instance_id = self.loop.run_until_complete(
            self.workflow.start_workflow("test_flow")
        )
        
        # Wait for completion
        while True:
            instance = self.workflow.get_instance(instance_id)
            if instance.state in (
                WorkflowState.COMPLETED,
                WorkflowState.FAILED
            ):
                break
            self.loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify context sharing
        self.assertEqual(instance.state, WorkflowState.COMPLETED)
        self.assertEqual(instance.context['value'], 42)

if __name__ == '__main__':
    unittest.main()
