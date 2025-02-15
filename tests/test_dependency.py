import unittest
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, List, Optional, Any, Type, TypeVar
from dataclasses import dataclass
from enum import Enum, auto
import inspect
import threading
from functools import wraps

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

T = TypeVar('T')

class DependencyScope(Enum):
    """Dependency scopes"""
    SINGLETON = auto()
    TRANSIENT = auto()
    SCOPED = auto()

class DependencyLifetime(Enum):
    """Dependency lifetimes"""
    PERMANENT = auto()
    REQUEST = auto()
    SESSION = auto()

@dataclass
class DependencyRegistration:
    """Dependency registration data"""
    interface: Type
    implementation: Type
    scope: DependencyScope
    lifetime: DependencyLifetime
    factory: Optional[callable] = None
    instance: Optional[Any] = None

class DependencyContainer:
    """Dependency container"""
    def __init__(self):
        self.registrations: Dict[Type, DependencyRegistration] = {}
        self.scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.Lock()

    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        scope: DependencyScope = DependencyScope.SINGLETON,
        lifetime: DependencyLifetime = DependencyLifetime.PERMANENT,
        factory: Optional[callable] = None
    ):
        """Register a dependency"""
        if implementation is None:
            implementation = interface
        
        registration = DependencyRegistration(
            interface=interface,
            implementation=implementation,
            scope=scope,
            lifetime=lifetime,
            factory=factory
        )
        
        if scope == DependencyScope.SINGLETON:
            if factory:
                registration.instance = factory()
            else:
                registration.instance = self._create_instance(implementation)
        
        self.registrations[interface] = registration

    def resolve(
        self,
        interface: Type[T],
        scope_id: Optional[str] = None
    ) -> T:
        """Resolve a dependency"""
        registration = self.registrations.get(interface)
        if not registration:
            raise KeyError(f"No registration found for {interface}")
        
        if registration.scope == DependencyScope.SINGLETON:
            return registration.instance
        
        elif registration.scope == DependencyScope.SCOPED:
            if not scope_id:
                raise ValueError("Scope ID required for scoped dependency")
            
            with self._lock:
                if scope_id not in self.scoped_instances:
                    self.scoped_instances[scope_id] = {}
                
                if interface not in self.scoped_instances[scope_id]:
                    if registration.factory:
                        instance = registration.factory()
                    else:
                        instance = self._create_instance(registration.implementation)
                    self.scoped_instances[scope_id][interface] = instance
                
                return self.scoped_instances[scope_id][interface]
        
        else:  # TRANSIENT
            if registration.factory:
                return registration.factory()
            return self._create_instance(registration.implementation)

    def begin_scope(self, scope_id: str):
        """Begin a dependency scope"""
        with self._lock:
            if scope_id in self.scoped_instances:
                raise ValueError(f"Scope {scope_id} already exists")
            self.scoped_instances[scope_id] = {}

    def end_scope(self, scope_id: str):
        """End a dependency scope"""
        with self._lock:
            if scope_id in self.scoped_instances:
                del self.scoped_instances[scope_id]

    def _create_instance(self, cls: Type[T]) -> T:
        """Create instance with dependencies"""
        if not inspect.isclass(cls):
            return cls
        
        # Get constructor parameters
        sig = inspect.signature(cls.__init__)
        params = {}
        
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            
            # Try to resolve dependency
            if param.annotation != inspect.Parameter.empty:
                try:
                    params[name] = self.resolve(param.annotation)
                except KeyError:
                    if param.default != inspect.Parameter.empty:
                        params[name] = param.default
                    else:
                        raise
        
        return cls(**params)

def inject(*dependencies):
    """Dependency injection decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            container = getattr(self, 'container', None)
            if not container:
                raise ValueError("No dependency container found")
            
            for dep in dependencies:
                setattr(self, f"_{dep.__name__}", container.resolve(dep))
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class TestDependency(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.container = DependencyContainer()

    def test_singleton_registration(self):
        """Test singleton dependency registration"""
        class Service:
            def get_data(self):
                return "data"
        
        # Register singleton
        self.container.register(Service)
        
        # Resolve multiple times
        instance1 = self.container.resolve(Service)
        instance2 = self.container.resolve(Service)
        
        # Verify same instance
        self.assertIs(instance1, instance2)

    def test_transient_registration(self):
        """Test transient dependency registration"""
        class Service:
            pass
        
        # Register transient
        self.container.register(
            Service,
            scope=DependencyScope.TRANSIENT
        )
        
        # Resolve multiple times
        instance1 = self.container.resolve(Service)
        instance2 = self.container.resolve(Service)
        
        # Verify different instances
        self.assertIsNot(instance1, instance2)

    def test_scoped_registration(self):
        """Test scoped dependency registration"""
        class Service:
            pass
        
        # Register scoped
        self.container.register(
            Service,
            scope=DependencyScope.SCOPED
        )
        
        # Create scopes
        self.container.begin_scope("scope1")
        self.container.begin_scope("scope2")
        
        # Resolve in different scopes
        instance1 = self.container.resolve(Service, "scope1")
        instance2 = self.container.resolve(Service, "scope1")
        instance3 = self.container.resolve(Service, "scope2")
        
        # Verify instances
        self.assertIs(instance1, instance2)  # Same scope
        self.assertIsNot(instance1, instance3)  # Different scope
        
        # Clean up
        self.container.end_scope("scope1")
        self.container.end_scope("scope2")

    def test_factory_registration(self):
        """Test factory registration"""
        class Service:
            def __init__(self, value: int):
                self.value = value
        
        # Register with factory
        self.container.register(
            Service,
            factory=lambda: Service(42)
        )
        
        # Resolve
        instance = self.container.resolve(Service)
        
        # Verify factory used
        self.assertEqual(instance.value, 42)

    def test_interface_implementation(self):
        """Test interface/implementation registration"""
        class IService:
            def get_data(self): pass
        
        class ServiceImpl(IService):
            def get_data(self):
                return "data"
        
        # Register implementation
        self.container.register(IService, ServiceImpl)
        
        # Resolve interface
        instance = self.container.resolve(IService)
        
        # Verify implementation
        self.assertIsInstance(instance, ServiceImpl)
        self.assertEqual(instance.get_data(), "data")

    def test_dependency_injection(self):
        """Test dependency injection"""
        class Database:
            def get_data(self):
                return "data"
        
        class Service:
            def __init__(self, db: Database):
                self.db = db
            
            def process(self):
                return self.db.get_data().upper()
        
        # Register dependencies
        self.container.register(Database)
        self.container.register(Service)
        
        # Resolve service
        service = self.container.resolve(Service)
        
        # Verify injection
        self.assertIsInstance(service.db, Database)
        self.assertEqual(service.process(), "DATA")

    def test_decorator_injection(self):
        """Test decorator-based injection"""
        class Service:
            def get_data(self):
                return "data"
        
        class Controller:
            def __init__(self, container: DependencyContainer):
                self.container = container
            
            @inject(Service)
            def process(self):
                return self._Service.get_data()
        
        # Register dependency
        self.container.register(Service)
        
        # Create controller
        controller = Controller(self.container)
        
        # Test injection
        self.assertEqual(controller.process(), "data")

    def test_scope_lifecycle(self):
        """Test scope lifecycle management"""
        class Service:
            def __init__(self):
                self.initialized = True
            
            def cleanup(self):
                self.initialized = False
        
        # Register scoped service
        self.container.register(
            Service,
            scope=DependencyScope.SCOPED
        )
        
        # Begin scope
        self.container.begin_scope("test_scope")
        
        # Use service
        service = self.container.resolve(Service, "test_scope")
        self.assertTrue(service.initialized)
        
        # End scope
        self.container.end_scope("test_scope")
        
        # Verify scope cleanup
        with self.assertRaises(ValueError):
            self.container.resolve(Service, "test_scope")

    def test_nested_dependencies(self):
        """Test nested dependency resolution"""
        class ServiceA:
            pass
        
        class ServiceB:
            def __init__(self, a: ServiceA):
                self.a = a
        
        class ServiceC:
            def __init__(self, b: ServiceB):
                self.b = b
        
        # Register dependencies
        self.container.register(ServiceA)
        self.container.register(ServiceB)
        self.container.register(ServiceC)
        
        # Resolve nested dependency
        service = self.container.resolve(ServiceC)
        
        # Verify resolution
        self.assertIsInstance(service.b, ServiceB)
        self.assertIsInstance(service.b.a, ServiceA)

    def test_optional_dependencies(self):
        """Test optional dependency handling"""
        class Service:
            def __init__(self, dep: Optional[str] = None):
                self.dep = dep
        
        # Register without optional dependency
        self.container.register(Service)
        
        # Resolve
        service = self.container.resolve(Service)
        
        # Verify optional dependency
        self.assertIsNone(service.dep)

if __name__ == '__main__':
    unittest.main()
