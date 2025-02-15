import unittest
from unittest.mock import Mock, patch
import sys
import os
import time
import threading
import multiprocessing
import asyncio
import websockets
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db
from models import User, Gate, Party
from game_manager import MainGameManager

class TestPerformance(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = self.app.test_client()
        self.game_manager = MainGameManager()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            self.users = []
            for i in range(100):
                user = User(
                    username=f'test_user_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user',
                    level=10
                )
                db.session.add(user)
                self.users.append(user)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_concurrent_requests(self):
        """Test handling of concurrent API requests"""
        num_requests = 1000
        num_threads = 10
        
        def make_request():
            return self.client.get('/api/status')
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            responses = list(executor.map(lambda _: make_request(), range(num_requests)))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate metrics
        successful_requests = sum(1 for r in responses if r.status_code == 200)
        requests_per_second = num_requests / duration
        
        print(f"\nConcurrent Requests Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Requests/second: {requests_per_second:.2f}")
        
        # Verify performance
        self.assertGreaterEqual(successful_requests / num_requests, 0.95)  # 95% success rate
        self.assertGreaterEqual(requests_per_second, 100)  # Minimum 100 req/s

    async def test_websocket_connections(self):
        """Test handling of multiple WebSocket connections"""
        num_connections = 100
        message_count = 50
        
        async def websocket_client():
            uri = "ws://localhost:5000/ws"
            async with websockets.connect(uri) as websocket:
                for _ in range(message_count):
                    await websocket.send("ping")
                    response = await websocket.recv()
                    self.assertEqual(response, "pong")
        
        start_time = time.time()
        
        # Create multiple WebSocket connections
        tasks = [websocket_client() for _ in range(num_connections)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_messages = num_connections * message_count
        messages_per_second = total_messages / duration
        
        print(f"\nWebSocket Connections Test Results:")
        print(f"Total Connections: {num_connections}")
        print(f"Messages per Connection: {message_count}")
        print(f"Total Messages: {total_messages}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Messages/second: {messages_per_second:.2f}")
        
        self.assertGreaterEqual(messages_per_second, 1000)  # Minimum 1000 msg/s

    def test_database_performance(self):
        """Test database query performance"""
        num_queries = 1000
        
        # Test read performance
        start_time = time.time()
        
        with self.app.app_context():
            for _ in range(num_queries):
                User.query.filter_by(level=10).all()
        
        read_duration = time.time() - start_time
        
        # Test write performance
        start_time = time.time()
        
        with self.app.app_context():
            for i in range(num_queries):
                user = User(
                    username=f'perf_test_user_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user'
                )
                db.session.add(user)
                if i % 100 == 0:  # Batch commits
                    db.session.commit()
            
            db.session.commit()
        
        write_duration = time.time() - start_time
        
        print(f"\nDatabase Performance Test Results:")
        print(f"Read Queries: {num_queries}")
        print(f"Read Duration: {read_duration:.2f} seconds")
        print(f"Reads/second: {num_queries/read_duration:.2f}")
        print(f"Write Operations: {num_queries}")
        print(f"Write Duration: {write_duration:.2f} seconds")
        print(f"Writes/second: {num_queries/write_duration:.2f}")
        
        self.assertLess(read_duration, 5)   # Max 5 seconds for reads
        self.assertLess(write_duration, 10)  # Max 10 seconds for writes

    def test_combat_system_performance(self):
        """Test combat system performance with multiple simultaneous battles"""
        num_battles = 100
        
        def simulate_battle():
            return self.game_manager.process_command(
                'gate_enter',
                self.users[0].id,
                {'gate_id': 1}
            )
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: simulate_battle(), range(num_battles)))
        
        duration = time.time() - start_time
        
        successful_battles = sum(1 for r in results if r['status'] == 'success')
        battles_per_second = num_battles / duration
        
        print(f"\nCombat System Performance Test Results:")
        print(f"Total Battles: {num_battles}")
        print(f"Successful Battles: {successful_battles}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Battles/second: {battles_per_second:.2f}")
        
        self.assertGreaterEqual(successful_battles / num_battles, 0.95)
        self.assertGreaterEqual(battles_per_second, 10)  # Minimum 10 battles/s

    def test_memory_usage(self):
        """Test memory usage under load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create load
        large_data = []
        for _ in range(1000):
            large_data.append('x' * 1000000)  # Allocate memory
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        
        # Cleanup
        del large_data
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"\nMemory Usage Test Results:")
        print(f"Initial Memory: {initial_memory:.2f} MB")
        print(f"Peak Memory: {peak_memory:.2f} MB")
        print(f"Final Memory: {final_memory:.2f} MB")
        print(f"Memory Leaked: {final_memory - initial_memory:.2f} MB")
        
        self.assertLess(final_memory - initial_memory, 10)  # Max 10MB leak

    def test_ai_system_performance(self):
        """Test AI system performance under load"""
        num_analyses = 100
        
        activity_history = [
            {'type': 'gate_hunting', 'success': True},
            {'type': 'trading', 'success': True},
            {'type': 'gambling', 'success': False}
        ]
        
        start_time = time.time()
        
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(
                lambda _: self.game_manager.game_systems.ai_system.analyze_player_behavior(
                    self.users[0].id,
                    activity_history
                ),
                range(num_analyses)
            ))
        
        duration = time.time() - start_time
        analyses_per_second = num_analyses / duration
        
        print(f"\nAI System Performance Test Results:")
        print(f"Total Analyses: {num_analyses}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Analyses/second: {analyses_per_second:.2f}")
        
        self.assertGreaterEqual(analyses_per_second, 50)  # Minimum 50 analyses/s

    def test_load_balancing(self):
        """Test load balancing capabilities"""
        num_requests = 1000
        endpoints = ['/api/status', '/api/users', '/api/gates']
        
        def make_request(endpoint):
            return self.client.get(endpoint)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(num_requests):
                endpoint = endpoints[_ % len(endpoints)]
                futures.append(executor.submit(make_request, endpoint))
            
            responses = [f.result() for f in futures]
        
        duration = time.time() - start_time
        
        # Calculate distribution
        endpoint_counts = {endpoint: 0 for endpoint in endpoints}
        for i, response in enumerate(responses):
            endpoint = endpoints[i % len(endpoints)]
            endpoint_counts[endpoint] += 1
        
        print(f"\nLoad Balancing Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Duration: {duration:.2f} seconds")
        print("Distribution:")
        for endpoint, count in endpoint_counts.items():
            print(f"{endpoint}: {count} requests")
        
        # Verify even distribution
        expected_count = num_requests / len(endpoints)
        for count in endpoint_counts.values():
            self.assertAlmostEqual(count, expected_count, delta=expected_count * 0.1)

if __name__ == '__main__':
    unittest.main()
