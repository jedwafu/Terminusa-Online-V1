import unittest
from unittest.mock import Mock, patch
import sys
import os
import time
import redis
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import User, Gate, Guild

class CacheManager:
    """Manages application caching"""
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = 3600  # 1 hour

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

    def delete(self, key: str):
        """Delete value from cache"""
        self.redis.delete(key)

    def clear(self):
        """Clear all cache"""
        self.redis.flushall()

def cached(ttl: int = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache_manager.get(key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Initialize cache manager
cache_manager = CacheManager()

class TestCaching(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Clear cache before each test
        cache_manager.clear()

    def test_basic_caching(self):
        """Test basic cache operations"""
        # Test setting and getting values
        cache_manager.set('test_key', 'test_value')
        value = cache_manager.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # Test TTL
        cache_manager.set('ttl_key', 'ttl_value', ttl=1)
        time.sleep(2)
        value = cache_manager.get('ttl_key')
        self.assertIsNone(value)
        
        # Test deletion
        cache_manager.set('delete_key', 'delete_value')
        cache_manager.delete('delete_key')
        value = cache_manager.get('delete_key')
        self.assertIsNone(value)

    def test_cached_decorator(self):
        """Test cached decorator functionality"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_operation(param):
            nonlocal call_count
            call_count += 1
            return f"Result for {param}"
        
        # First call should execute function
        result1 = expensive_operation("test")
        self.assertEqual(call_count, 1)
        
        # Second call should use cache
        result2 = expensive_operation("test")
        self.assertEqual(call_count, 1)
        self.assertEqual(result1, result2)

    def test_model_caching(self):
        """Test model data caching"""
        with self.app.app_context():
            # Create test user
            user = User(
                username='test_user',
                password='hashed_password',
                salt='test_salt',
                role='user'
            )
            
            # Cache user data
            cache_manager.set(
                f'user:{user.username}',
                {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            )
            
            # Retrieve from cache
            cached_user = cache_manager.get(f'user:{user.username}')
            self.assertEqual(cached_user['username'], user.username)

    def test_cache_invalidation(self):
        """Test cache invalidation strategies"""
        def invalidate_user_cache(user_id: int):
            """Invalidate user-related caches"""
            patterns = [
                f'user:{user_id}',
                f'user:{user_id}:profile',
                f'user:{user_id}:inventory'
            ]
            for pattern in patterns:
                cache_manager.delete(pattern)
        
        # Set up test data
        user_id = 1
        cache_manager.set(f'user:{user_id}', {'name': 'test'})
        cache_manager.set(f'user:{user_id}:profile', {'level': 10})
        
        # Invalidate caches
        invalidate_user_cache(user_id)
        
        # Verify invalidation
        self.assertIsNone(cache_manager.get(f'user:{user_id}'))
        self.assertIsNone(cache_manager.get(f'user:{user_id}:profile'))

    def test_cache_patterns(self):
        """Test different caching patterns"""
        # Write-through cache
        def save_user_write_through(user_data):
            """Save user with write-through caching"""
            # Save to database
            user = User(**user_data)
            
            # Update cache immediately
            cache_manager.set(
                f'user:{user.id}',
                user_data
            )
            
            return user
        
        # Write-behind cache
        def save_user_write_behind(user_data):
            """Save user with write-behind caching"""
            # Update cache immediately
            cache_key = f'user:{user_data["id"]}'
            cache_manager.set(cache_key, user_data)
            
            # Queue database update
            self._queue_db_update('user', user_data)
        
        # Cache-aside
        def get_user_cache_aside(user_id):
            """Get user with cache-aside pattern"""
            # Try cache first
            cached_user = cache_manager.get(f'user:{user_id}')
            if cached_user:
                return cached_user
            
            # Load from database
            user = User.query.get(user_id)
            if user:
                # Update cache
                cache_manager.set(
                    f'user:{user_id}',
                    user.__dict__
                )
                return user.__dict__
            
            return None

    def test_cache_performance(self):
        """Test cache performance"""
        # Generate test data
        test_data = {str(i): f"value_{i}" for i in range(1000)}
        
        # Measure cache write performance
        start_time = time.time()
        for key, value in test_data.items():
            cache_manager.set(key, value)
        write_time = time.time() - start_time
        
        # Measure cache read performance
        start_time = time.time()
        for key in test_data:
            cache_manager.get(key)
        read_time = time.time() - start_time
        
        # Verify performance
        self.assertLess(write_time, 1.0)  # Write within 1 second
        self.assertLess(read_time, 0.5)   # Read within 0.5 seconds

    def test_cache_consistency(self):
        """Test cache consistency mechanisms"""
        def update_with_version(key, value, version):
            """Update cache with version control"""
            current = cache_manager.get(key)
            if current and current.get('version', 0) > version:
                return False  # Stale update
            
            cache_manager.set(key, {
                'data': value,
                'version': version
            })
            return True
        
        # Test version control
        key = 'versioned_data'
        self.assertTrue(update_with_version(key, 'value1', 1))
        self.assertFalse(update_with_version(key, 'value2', 0))  # Stale
        self.assertTrue(update_with_version(key, 'value3', 2))   # Newer

    def test_distributed_caching(self):
        """Test distributed caching scenarios"""
        def acquire_lock(key, timeout=10):
            """Acquire distributed lock"""
            lock_key = f"lock:{key}"
            return cache_manager.redis.set(
                lock_key,
                'locked',
                ex=timeout,
                nx=True
            )
        
        def release_lock(key):
            """Release distributed lock"""
            lock_key = f"lock:{key}"
            cache_manager.redis.delete(lock_key)
        
        # Test distributed locking
        key = 'shared_resource'
        self.assertTrue(acquire_lock(key))
        self.assertFalse(acquire_lock(key))  # Already locked
        release_lock(key)
        self.assertTrue(acquire_lock(key))    # Lock released

    def _queue_db_update(self, model: str, data: dict):
        """Mock function for queuing database updates"""
        pass

if __name__ == '__main__':
    unittest.main()
