import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto
import time
import redis

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RateLimitType(Enum):
    """Rate limit types"""
    REQUESTS = auto()
    ACTIONS = auto()
    LOGIN = auto()
    API = auto()
    WEBSOCKET = auto()

@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit: int
    window: int  # seconds
    block_duration: Optional[int] = None  # seconds to block after limit exceeded

class RateLimitExceeded(Exception):
    """Rate limit exceeded exception"""
    def __init__(self, limit_type: RateLimitType, retry_after: int):
        self.limit_type = limit_type
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for {limit_type.name}. "
            f"Try again in {retry_after} seconds"
        )

class RateLimitSystem:
    """Rate limiting system"""
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url)
        self.limits: Dict[RateLimitType, RateLimit] = {
            RateLimitType.REQUESTS: RateLimit(1000, 3600),  # 1000 per hour
            RateLimitType.ACTIONS: RateLimit(100, 60),      # 100 per minute
            RateLimitType.LOGIN: RateLimit(5, 300, 900),    # 5 per 5 minutes, block 15 minutes
            RateLimitType.API: RateLimit(60, 60),           # 60 per minute
            RateLimitType.WEBSOCKET: RateLimit(100, 60)     # 100 per minute
        }

    def check_rate_limit(
        self,
        key: str,
        limit_type: RateLimitType
    ) -> bool:
        """Check if action is within rate limit"""
        if limit_type not in self.limits:
            return True
        
        limit = self.limits[limit_type]
        
        # Check if blocked
        block_key = f"block:{limit_type.name}:{key}"
        if self.redis.exists(block_key):
            block_ttl = self.redis.ttl(block_key)
            raise RateLimitExceeded(limit_type, block_ttl)
        
        # Get current count
        count_key = f"count:{limit_type.name}:{key}"
        current = int(self.redis.get(count_key) or 0)
        
        if current >= limit.limit:
            # Apply block if configured
            if limit.block_duration:
                self.redis.setex(
                    block_key,
                    limit.block_duration,
                    1
                )
            
            # Get time until reset
            ttl = self.redis.ttl(count_key)
            raise RateLimitExceeded(limit_type, ttl)
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(count_key)
        if not self.redis.exists(count_key):
            pipe.expire(count_key, limit.window)
        pipe.execute()
        
        return True

    def reset_limits(self, key: str, limit_type: Optional[RateLimitType] = None):
        """Reset rate limits for key"""
        if limit_type:
            self.redis.delete(
                f"count:{limit_type.name}:{key}",
                f"block:{limit_type.name}:{key}"
            )
        else:
            for limit_type in RateLimitType:
                self.redis.delete(
                    f"count:{limit_type.name}:{key}",
                    f"block:{limit_type.name}:{key}"
                )

    def update_limit(self, limit_type: RateLimitType, limit: RateLimit):
        """Update rate limit configuration"""
        self.limits[limit_type] = limit

class TestRateLimiting(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.rate_limiter = RateLimitSystem()
        self.test_key = "test_user"

    def tearDown(self):
        """Clean up after each test"""
        self.rate_limiter.reset_limits(self.test_key)

    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality"""
        # Test within limit
        for _ in range(5):
            self.assertTrue(
                self.rate_limiter.check_rate_limit(
                    self.test_key,
                    RateLimitType.LOGIN
                )
            )
        
        # Test exceeding limit
        with self.assertRaises(RateLimitExceeded) as context:
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )
        
        self.assertEqual(context.exception.limit_type, RateLimitType.LOGIN)

    def test_blocking(self):
        """Test blocking after limit exceeded"""
        # Exceed login limit
        for _ in range(5):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )
        
        # Verify blocked
        with self.assertRaises(RateLimitExceeded) as context:
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )
        
        # Verify block duration
        self.assertGreater(context.exception.retry_after, 0)

    def test_different_types(self):
        """Test different rate limit types"""
        # Test API limits
        for _ in range(60):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.API
            )
        
        with self.assertRaises(RateLimitExceeded):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.API
            )
        
        # Test action limits (should be independent)
        self.assertTrue(
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.ACTIONS
            )
        )

    def test_limit_reset(self):
        """Test rate limit reset"""
        # Use some limits
        for _ in range(3):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )
        
        # Reset limits
        self.rate_limiter.reset_limits(
            self.test_key,
            RateLimitType.LOGIN
        )
        
        # Should be able to use full limit again
        for _ in range(5):
            self.assertTrue(
                self.rate_limiter.check_rate_limit(
                    self.test_key,
                    RateLimitType.LOGIN
                )
            )

    def test_limit_update(self):
        """Test updating rate limits"""
        # Update login limit
        new_limit = RateLimit(
            limit=2,
            window=60,
            block_duration=120
        )
        self.rate_limiter.update_limit(RateLimitType.LOGIN, new_limit)
        
        # Test new limit
        for _ in range(2):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )
        
        with self.assertRaises(RateLimitExceeded):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )

    def test_multiple_users(self):
        """Test rate limiting for multiple users"""
        user1 = "user1"
        user2 = "user2"
        
        try:
            # Test limits independently
            for _ in range(5):
                self.rate_limiter.check_rate_limit(
                    user1,
                    RateLimitType.LOGIN
                )
            
            # Second user should still have full limit
            for _ in range(5):
                self.assertTrue(
                    self.rate_limiter.check_rate_limit(
                        user2,
                        RateLimitType.LOGIN
                    )
                )
        finally:
            self.rate_limiter.reset_limits(user1)
            self.rate_limiter.reset_limits(user2)

    def test_window_expiration(self):
        """Test rate limit window expiration"""
        # Create short window limit
        self.rate_limiter.update_limit(
            RateLimitType.ACTIONS,
            RateLimit(limit=1, window=1)  # 1 second window
        )
        
        # Use limit
        self.rate_limiter.check_rate_limit(
            self.test_key,
            RateLimitType.ACTIONS
        )
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be able to use limit again
        self.assertTrue(
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.ACTIONS
            )
        )

    def test_websocket_limits(self):
        """Test WebSocket rate limiting"""
        # Test normal usage
        for _ in range(100):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.WEBSOCKET
            )
        
        # Test exceeding limit
        with self.assertRaises(RateLimitExceeded):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.WEBSOCKET
            )

    def test_api_burst(self):
        """Test API burst handling"""
        # Simulate API burst
        for _ in range(10):
            for _ in range(6):  # 60 requests in total
                self.rate_limiter.check_rate_limit(
                    self.test_key,
                    RateLimitType.API
                )
            time.sleep(0.1)  # Small delay between bursts
        
        # Verify limit exceeded
        with self.assertRaises(RateLimitExceeded):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.API
            )

    def test_distributed_rate_limiting(self):
        """Test rate limiting across multiple instances"""
        # Simulate multiple instances
        instance1 = RateLimitSystem()
        instance2 = RateLimitSystem()
        
        try:
            # Use limits from both instances
            for _ in range(3):
                instance1.check_rate_limit(
                    self.test_key,
                    RateLimitType.LOGIN
                )
            
            for _ in range(2):
                instance2.check_rate_limit(
                    self.test_key,
                    RateLimitType.LOGIN
                )
            
            # Verify limit is shared
            with self.assertRaises(RateLimitExceeded):
                instance1.check_rate_limit(
                    self.test_key,
                    RateLimitType.LOGIN
                )
        finally:
            instance1.reset_limits(self.test_key)
            instance2.reset_limits(self.test_key)

    def test_rate_limit_info(self):
        """Test rate limit information"""
        # Use some of the limit
        for _ in range(3):
            self.rate_limiter.check_rate_limit(
                self.test_key,
                RateLimitType.LOGIN
            )
        
        # Get remaining limit
        count_key = f"count:LOGIN:{self.test_key}"
        used = int(self.rate_limiter.redis.get(count_key) or 0)
        limit = self.rate_limiter.limits[RateLimitType.LOGIN].limit
        
        self.assertEqual(used, 3)
        self.assertEqual(limit - used, 2)  # 2 remaining

if __name__ == '__main__':
    unittest.main()
