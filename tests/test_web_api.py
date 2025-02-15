import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import jwt
import asyncio
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APIError(Exception):
    """API error with status code"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code

class WebAPI:
    """Web API handler"""
    def __init__(self, app: web.Application):
        self.app = app
        self.jwt_secret = "test-secret-key"
        self.rate_limits = {
            'default': 100,  # requests per minute
            'auth': 10,
            'game_action': 200
        }

    async def setup_routes(self):
        """Set up API routes"""
        # Auth routes
        self.app.router.add_post('/api/auth/login', self.handle_login)
        self.app.router.add_post('/api/auth/register', self.handle_register)
        self.app.router.add_post('/api/auth/refresh', self.handle_refresh)
        
        # Player routes
        self.app.router.add_get('/api/player/{id}', self.handle_get_player)
        self.app.router.add_put('/api/player/{id}', self.handle_update_player)
        self.app.router.add_get('/api/player/{id}/inventory', self.handle_get_inventory)
        
        # Game routes
        self.app.router.add_post('/api/game/action', self.handle_game_action)
        self.app.router.add_get('/api/game/status', self.handle_game_status)
        
        # Admin routes
        self.app.router.add_get('/api/admin/metrics', self.handle_admin_metrics)
        self.app.router.add_post('/api/admin/maintenance', self.handle_maintenance)

    @web.middleware
    async def auth_middleware(self, request: web.Request, handler):
        """Authentication middleware"""
        # Skip auth for public endpoints
        if request.path in ['/api/auth/login', '/api/auth/register']:
            return await handler(request)
        
        # Verify token
        try:
            auth = request.headers.get('Authorization')
            if not auth or not auth.startswith('Bearer '):
                raise APIError('Missing authentication', 401)
            
            token = auth.split(' ')[1]
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256']
            )
            
            request['user_id'] = payload['user_id']
            return await handler(request)
            
        except jwt.InvalidTokenError:
            raise APIError('Invalid token', 401)

    @web.middleware
    async def rate_limit_middleware(self, request: web.Request, handler):
        """Rate limiting middleware"""
        # Get rate limit for endpoint
        path = request.path
        if path.startswith('/api/auth/'):
            limit = self.rate_limits['auth']
        elif path.startswith('/api/game/action'):
            limit = self.rate_limits['game_action']
        else:
            limit = self.rate_limits['default']
        
        # Check rate limit (simplified)
        # In production would use Redis/memcached
        key = f"{request.remote}:{path}"
        current = getattr(request.app, '_rate_limits', {}).get(key, 0)
        
        if current >= limit:
            raise APIError('Rate limit exceeded', 429)
        
        if not hasattr(request.app, '_rate_limits'):
            request.app._rate_limits = {}
        request.app._rate_limits[key] = current + 1
        
        return await handler(request)

    async def handle_login(self, request: web.Request) -> web.Response:
        """Handle login request"""
        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                raise APIError('Missing credentials')
            
            # Authenticate (mock)
            user_id = 1
            
            # Generate token
            token = jwt.encode(
                {
                    'user_id': user_id,
                    'exp': datetime.utcnow() + timedelta(days=1)
                },
                self.jwt_secret,
                algorithm='HS256'
            )
            
            return web.json_response({
                'token': token,
                'user_id': user_id
            })
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

    async def handle_register(self, request: web.Request) -> web.Response:
        """Handle registration request"""
        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            
            if not all([username, password, email]):
                raise APIError('Missing required fields')
            
            # Register user (mock)
            user_id = 1
            
            return web.json_response({
                'user_id': user_id,
                'message': 'Registration successful'
            })
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

    async def handle_refresh(self, request: web.Request) -> web.Response:
        """Handle token refresh request"""
        try:
            data = await request.json()
            old_token = data.get('token')
            
            if not old_token:
                raise APIError('Missing token')
            
            # Verify old token
            try:
                payload = jwt.decode(
                    old_token,
                    self.jwt_secret,
                    algorithms=['HS256']
                )
            except jwt.InvalidTokenError:
                raise APIError('Invalid token', 401)
            
            # Generate new token
            new_token = jwt.encode(
                {
                    'user_id': payload['user_id'],
                    'exp': datetime.utcnow() + timedelta(days=1)
                },
                self.jwt_secret,
                algorithm='HS256'
            )
            
            return web.json_response({'token': new_token})
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

    async def handle_get_player(self, request: web.Request) -> web.Response:
        """Handle get player request"""
        try:
            player_id = int(request.match_info['id'])
            
            # Get player data (mock)
            player_data = {
                'id': player_id,
                'username': f'player_{player_id}',
                'level': 10,
                'experience': 1000
            }
            
            return web.json_response(player_data)
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

    async def handle_update_player(self, request: web.Request) -> web.Response:
        """Handle update player request"""
        try:
            player_id = int(request.match_info['id'])
            data = await request.json()
            
            # Verify ownership
            if player_id != request['user_id']:
                raise APIError('Unauthorized', 403)
            
            # Update player (mock)
            return web.json_response({
                'message': 'Player updated successfully'
            })
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

    async def handle_game_action(self, request: web.Request) -> web.Response:
        """Handle game action request"""
        try:
            data = await request.json()
            action = data.get('action')
            parameters = data.get('parameters', {})
            
            if not action:
                raise APIError('Missing action')
            
            # Process action (mock)
            result = {
                'success': True,
                'action': action,
                'result': 'Action processed successfully'
            }
            
            return web.json_response(result)
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

    async def handle_game_status(self, request: web.Request) -> web.Response:
        """Handle game status request"""
        try:
            # Get game status (mock)
            status = {
                'online_players': 100,
                'server_status': 'running',
                'uptime': '24h'
            }
            
            return web.json_response(status)
            
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            return web.json_response(
                {'error': str(e)},
                status=status
            )

class TestWebAPI(AioHTTPTestCase):
    async def get_application(self):
        """Create application for testing"""
        app = web.Application(
            middlewares=[
                WebAPI.auth_middleware,
                WebAPI.rate_limit_middleware
            ]
        )
        api = WebAPI(app)
        await api.setup_routes()
        return app

    @unittest_run_loop
    async def test_login(self):
        """Test login endpoint"""
        # Test successful login
        resp = await self.client.post(
            '/api/auth/login',
            json={
                'username': 'test_user',
                'password': 'test_pass'
            }
        )
        
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIn('token', data)
        
        # Test invalid credentials
        resp = await self.client.post(
            '/api/auth/login',
            json={
                'username': 'test_user'
                # Missing password
            }
        )
        
        self.assertEqual(resp.status, 400)

    @unittest_run_loop
    async def test_register(self):
        """Test registration endpoint"""
        # Test successful registration
        resp = await self.client.post(
            '/api/auth/register',
            json={
                'username': 'new_user',
                'password': 'new_pass',
                'email': 'test@example.com'
            }
        )
        
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIn('user_id', data)

    @unittest_run_loop
    async def test_protected_endpoints(self):
        """Test protected endpoints"""
        # Get token
        resp = await self.client.post(
            '/api/auth/login',
            json={
                'username': 'test_user',
                'password': 'test_pass'
            }
        )
        token = (await resp.json())['token']
        
        # Test with token
        resp = await self.client.get(
            '/api/player/1',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(resp.status, 200)
        
        # Test without token
        resp = await self.client.get('/api/player/1')
        self.assertEqual(resp.status, 401)

    @unittest_run_loop
    async def test_rate_limiting(self):
        """Test rate limiting"""
        # Make many requests
        for _ in range(15):  # Over auth limit
            await self.client.post(
                '/api/auth/login',
                json={
                    'username': 'test_user',
                    'password': 'test_pass'
                }
            )
        
        # Verify rate limit
        resp = await self.client.post(
            '/api/auth/login',
            json={
                'username': 'test_user',
                'password': 'test_pass'
            }
        )
        
        self.assertEqual(resp.status, 429)

    @unittest_run_loop
    async def test_game_actions(self):
        """Test game action endpoint"""
        # Get token
        resp = await self.client.post(
            '/api/auth/login',
            json={
                'username': 'test_user',
                'password': 'test_pass'
            }
        )
        token = (await resp.json())['token']
        
        # Test game action
        resp = await self.client.post(
            '/api/game/action',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'action': 'move',
                'parameters': {'x': 100, 'y': 200}
            }
        )
        
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data['success'])

    @unittest_run_loop
    async def test_error_handling(self):
        """Test error handling"""
        # Test invalid JSON
        resp = await self.client.post(
            '/api/auth/login',
            data='invalid json'
        )
        
        self.assertEqual(resp.status, 400)
        
        # Test invalid endpoint
        resp = await self.client.get('/api/invalid')
        self.assertEqual(resp.status, 404)

if __name__ == '__main__':
    unittest.main()
