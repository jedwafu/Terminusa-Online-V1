import unittest
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from enum import Enum, auto
import importlib.util
import inspect
import json
import threading

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PluginState(Enum):
    """Plugin states"""
    DISABLED = auto()
    ENABLED = auto()
    ERROR = auto()

class PluginPriority(Enum):
    """Plugin priorities"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class PluginInfo:
    """Plugin information"""
    id: str
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    hooks: List[str]
    priority: PluginPriority
    config: Dict[str, Any]

@dataclass
class Plugin:
    """Plugin data"""
    info: PluginInfo
    module: Any
    state: PluginState
    instance: Optional[Any] = None

class PluginHook:
    """Plugin hook decorator"""
    def __init__(self, name: str):
        self.name = name
        self.handlers = []

    def __call__(self, func):
        self.handlers.append(func)
        return func

    def execute(self, *args, **kwargs):
        """Execute all handlers for this hook"""
        results = []
        for handler in sorted(
            self.handlers,
            key=lambda h: getattr(
                h.__self__,
                'priority',
                PluginPriority.NORMAL
            ).value,
            reverse=True
        ):
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error in plugin hook {self.name}: {e}")
        return results

class PluginSystem:
    """System for plugin management"""
    def __init__(self, plugins_dir: str = 'plugins'):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, PluginHook] = {}
        self._lock = threading.Lock()

    def load_plugins(self):
        """Load all plugins from directory"""
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        for entry in os.scandir(self.plugins_dir):
            if entry.is_dir() and not entry.name.startswith('_'):
                self.load_plugin(entry.name)

    def load_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Load a specific plugin"""
        plugin_dir = os.path.join(self.plugins_dir, plugin_id)
        if not os.path.isdir(plugin_dir):
            return None
        
        # Load plugin info
        info_path = os.path.join(plugin_dir, 'plugin.json')
        if not os.path.exists(info_path):
            return None
        
        with open(info_path, 'r') as f:
            info_data = json.load(f)
            info = PluginInfo(
                id=plugin_id,
                name=info_data['name'],
                version=info_data['version'],
                description=info_data['description'],
                author=info_data['author'],
                dependencies=info_data.get('dependencies', []),
                hooks=info_data.get('hooks', []),
                priority=PluginPriority[info_data.get(
                    'priority',
                    'NORMAL'
                )],
                config=info_data.get('config', {})
            )
        
        # Load plugin module
        module_path = os.path.join(plugin_dir, 'plugin.py')
        if not os.path.exists(module_path):
            return None
        
        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_id}",
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Create plugin
        plugin = Plugin(
            info=info,
            module=module,
            state=PluginState.DISABLED
        )
        
        self.plugins[plugin_id] = plugin
        return plugin

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False
        
        # Check dependencies
        for dep_id in plugin.info.dependencies:
            dep = self.plugins.get(dep_id)
            if not dep or dep.state != PluginState.ENABLED:
                return False
        
        try:
            # Create instance if needed
            if hasattr(plugin.module, 'Plugin'):
                plugin.instance = plugin.module.Plugin()
            
            # Register hooks
            self._register_hooks(plugin)
            
            plugin.state = PluginState.ENABLED
            return True
            
        except Exception:
            plugin.state = PluginState.ERROR
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False
        
        # Check for dependent plugins
        for other in self.plugins.values():
            if (plugin_id in other.info.dependencies and
                other.state == PluginState.ENABLED):
                return False
        
        # Unregister hooks
        self._unregister_hooks(plugin)
        
        plugin.state = PluginState.DISABLED
        return True

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get plugin by ID"""
        return self.plugins.get(plugin_id)

    def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins"""
        return [
            p for p in self.plugins.values()
            if p.state == PluginState.ENABLED
        ]

    def register_hook(self, name: str) -> PluginHook:
        """Register a new hook"""
        if name not in self.hooks:
            self.hooks[name] = PluginHook(name)
        return self.hooks[name]

    def execute_hook(
        self,
        name: str,
        *args,
        **kwargs
    ) -> List[Any]:
        """Execute a hook"""
        hook = self.hooks.get(name)
        if not hook:
            return []
        return hook.execute(*args, **kwargs)

    def _register_hooks(self, plugin: Plugin):
        """Register plugin hooks"""
        if not plugin.instance:
            return
        
        for name in plugin.info.hooks:
            if hasattr(plugin.instance, name):
                hook = self.register_hook(name)
                hook.handlers.append(
                    getattr(plugin.instance, name)
                )

    def _unregister_hooks(self, plugin: Plugin):
        """Unregister plugin hooks"""
        if not plugin.instance:
            return
        
        for name in plugin.info.hooks:
            hook = self.hooks.get(name)
            if hook and hasattr(plugin.instance, name):
                handler = getattr(plugin.instance, name)
                if handler in hook.handlers:
                    hook.handlers.remove(handler)

class TestPlugins(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.plugins_dir = 'test_plugins'
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.plugin_system = PluginSystem(self.plugins_dir)

    def tearDown(self):
        """Clean up after each test"""
        import shutil
        if os.path.exists(self.plugins_dir):
            shutil.rmtree(self.plugins_dir)

    def test_plugin_loading(self):
        """Test plugin loading"""
        # Create test plugin
        plugin_dir = os.path.join(self.plugins_dir, 'test_plugin')
        os.makedirs(plugin_dir)
        
        # Create plugin info
        with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
            json.dump({
                'name': 'Test Plugin',
                'version': '1.0.0',
                'description': 'Test plugin',
                'author': 'Test Author',
                'hooks': ['on_event']
            }, f)
        
        # Create plugin module
        with open(os.path.join(plugin_dir, 'plugin.py'), 'w') as f:
            f.write("""
class Plugin:
    def on_event(self, data):
        return f"Processed: {data}"
""")
        
        # Load plugin
        plugin = self.plugin_system.load_plugin('test_plugin')
        
        # Verify loading
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.info.name, 'Test Plugin')
        self.assertEqual(plugin.state, PluginState.DISABLED)

    def test_plugin_enabling(self):
        """Test plugin enabling"""
        # Create and load plugin
        plugin_dir = os.path.join(self.plugins_dir, 'test_plugin')
        os.makedirs(plugin_dir)
        
        with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
            json.dump({
                'name': 'Test Plugin',
                'version': '1.0.0',
                'description': 'Test plugin',
                'author': 'Test Author',
                'hooks': ['on_event']
            }, f)
        
        with open(os.path.join(plugin_dir, 'plugin.py'), 'w') as f:
            f.write("""
class Plugin:
    def on_event(self, data):
        return f"Processed: {data}"
""")
        
        self.plugin_system.load_plugin('test_plugin')
        
        # Enable plugin
        success = self.plugin_system.enable_plugin('test_plugin')
        
        # Verify enabling
        self.assertTrue(success)
        plugin = self.plugin_system.get_plugin('test_plugin')
        self.assertEqual(plugin.state, PluginState.ENABLED)

    def test_hook_execution(self):
        """Test plugin hook execution"""
        # Create and load plugin
        plugin_dir = os.path.join(self.plugins_dir, 'test_plugin')
        os.makedirs(plugin_dir)
        
        with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
            json.dump({
                'name': 'Test Plugin',
                'version': '1.0.0',
                'description': 'Test plugin',
                'author': 'Test Author',
                'hooks': ['on_event']
            }, f)
        
        with open(os.path.join(plugin_dir, 'plugin.py'), 'w') as f:
            f.write("""
class Plugin:
    def on_event(self, data):
        return f"Processed: {data}"
""")
        
        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.enable_plugin('test_plugin')
        
        # Execute hook
        results = self.plugin_system.execute_hook(
            'on_event',
            'test_data'
        )
        
        # Verify execution
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "Processed: test_data")

    def test_plugin_dependencies(self):
        """Test plugin dependencies"""
        # Create base plugin
        base_dir = os.path.join(self.plugins_dir, 'base_plugin')
        os.makedirs(base_dir)
        
        with open(os.path.join(base_dir, 'plugin.json'), 'w') as f:
            json.dump({
                'name': 'Base Plugin',
                'version': '1.0.0',
                'description': 'Base plugin',
                'author': 'Test Author',
                'hooks': []
            }, f)
        
        with open(os.path.join(base_dir, 'plugin.py'), 'w') as f:
            f.write("class Plugin: pass")
        
        # Create dependent plugin
        dep_dir = os.path.join(self.plugins_dir, 'dep_plugin')
        os.makedirs(dep_dir)
        
        with open(os.path.join(dep_dir, 'plugin.json'), 'w') as f:
            json.dump({
                'name': 'Dependent Plugin',
                'version': '1.0.0',
                'description': 'Dependent plugin',
                'author': 'Test Author',
                'dependencies': ['base_plugin'],
                'hooks': []
            }, f)
        
        with open(os.path.join(dep_dir, 'plugin.py'), 'w') as f:
            f.write("class Plugin: pass")
        
        # Load plugins
        self.plugin_system.load_plugin('base_plugin')
        self.plugin_system.load_plugin('dep_plugin')
        
        # Try to enable dependent plugin first
        success = self.plugin_system.enable_plugin('dep_plugin')
        self.assertFalse(success)  # Should fail
        
        # Enable base plugin first
        self.plugin_system.enable_plugin('base_plugin')
        success = self.plugin_system.enable_plugin('dep_plugin')
        self.assertTrue(success)  # Should succeed

    def test_plugin_priority(self):
        """Test plugin priority handling"""
        # Create plugins with different priorities
        priorities = ['HIGH', 'LOW']
        
        for i, priority in enumerate(priorities):
            plugin_dir = os.path.join(
                self.plugins_dir,
                f'plugin_{i}'
            )
            os.makedirs(plugin_dir)
            
            with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
                json.dump({
                    'name': f'Plugin {i}',
                    'version': '1.0.0',
                    'description': f'Plugin {i}',
                    'author': 'Test Author',
                    'priority': priority,
                    'hooks': ['on_event']
                }, f)
            
            with open(os.path.join(plugin_dir, 'plugin.py'), 'w') as f:
                f.write(f"""
class Plugin:
    def on_event(self, data):
        return f"Plugin {i}: {{data}}"
""")
            
            self.plugin_system.load_plugin(f'plugin_{i}')
            self.plugin_system.enable_plugin(f'plugin_{i}')
        
        # Execute hook
        results = self.plugin_system.execute_hook(
            'on_event',
            'test'
        )
        
        # Verify priority order
        self.assertEqual(results[0], "Plugin 0: test")  # HIGH
        self.assertEqual(results[1], "Plugin 1: test")  # LOW

if __name__ == '__main__':
    unittest.main()
