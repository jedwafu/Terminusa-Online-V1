import asyncio
import json
import logging
import psutil
import redis
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
from websockets.server import WebSocketServerProtocol

from models import db, User, Guild, GuildWar
from game_systems.event_system import EventSystem, EventType, GameEvent

logger = logging.getLogger(__name__)

class MonitoringWebSocket:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.clients = set()
        self.update_task = None
        self.event_system = EventSystem(websocket_manager)
        
        # Initialize connections
        self.init_connections()

    def init_connections(self):
        """Initialize database and cache connections"""
        try:
            self.redis = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise

    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle new WebSocket connection"""
        try:
            # Verify admin access
            if not await self.verify_admin(websocket):
                await websocket.close(1008, "Unauthorized")
                return

            # Add client to set
            self.clients.add(websocket)
            
            # Start update task if not running
            if not self.update_task or self.update_task.done():
                self.update_task = asyncio.create_task(self.send_updates())

            try:
                # Keep connection alive and handle messages
                async for message in websocket:
                    await self.handle_message(websocket, message)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                
            finally:
                # Remove client and cancel task if no clients left
                self.clients.remove(websocket)
                if not self.clients and self.update_task:
                    self.update_task.cancel()
                    
        except Exception as e:
            logger.error(f"Connection handler error: {e}")

    async def verify_admin(self, websocket: WebSocketServerProtocol) -> bool:
        """Verify admin access token"""
        try:
            token = websocket.request_headers.get('Authorization', '').split(' ')[1]
            return bool(token and self.verify_admin_token(token))
        except Exception:
            return False

    def verify_admin_token(self, token: str) -> bool:
        """Verify admin token validity"""
        try:
            # Check token in Redis
            admin_data = self.redis.get(f"admin_token:{token}")
            return bool(admin_data)
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'subscribe':
                await self.handle_subscribe(websocket, data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscribe(websocket, data)
            elif message_type == 'acknowledge_alert':
                await self.handle_acknowledge_alert(data)

        except Exception as e:
            logger.error(f"Message handler error: {e}")
            await self.send_error(websocket, str(e))

    async def handle_subscribe(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle subscription requests"""
        try:
            metrics = data.get('metrics', [])
            if not websocket.subscriptions:
                websocket.subscriptions = set()
            websocket.subscriptions.update(metrics)
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            await self.send_error(websocket, "Failed to subscribe")

    async def handle_unsubscribe(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle unsubscription requests"""
        try:
            metrics = data.get('metrics', [])
            if hasattr(websocket, 'subscriptions'):
                websocket.subscriptions.difference_update(metrics)
                
        except Exception as e:
            logger.error(f"Unsubscription error: {e}")
            await self.send_error(websocket, "Failed to unsubscribe")

    async def handle_acknowledge_alert(self, data: Dict):
        """Handle alert acknowledgment"""
        try:
            alert_id = data.get('alert_id')
            if alert_id:
                # Update alert status in database
                self.acknowledge_alert(alert_id)
                
                # Notify all clients
                await self.broadcast({
                    'type': 'alert_acknowledged',
                    'alert_id': alert_id
                })
                
        except Exception as e:
            logger.error(f"Alert acknowledgment error: {e}")

    async def send_updates(self):
        """Send periodic updates to all connected clients"""
        try:
            while True:
                metrics = self.collect_metrics()
                
                for websocket in self.clients:
                    try:
                        # Filter metrics based on subscriptions
                        if hasattr(websocket, 'subscriptions'):
                            filtered_metrics = {
                                k: v for k, v in metrics.items()
                                if k in websocket.subscriptions
                            }
                        else:
                            filtered_metrics = metrics

                        await websocket.send(json.dumps({
                            'type': 'metrics',
                            'timestamp': datetime.utcnow().isoformat(),
                            'data': filtered_metrics
                        }))
                        
                    except Exception as e:
                        logger.error(f"Failed to send update to client: {e}")
                        
                await asyncio.sleep(1)  # Update every second
                
        except asyncio.CancelledError:
            logger.info("Update task cancelled")
        except Exception as e:
            logger.error(f"Update task error: {e}")

    def collect_metrics(self) -> Dict:
        """Collect all monitoring metrics"""
        try:
            return {
                'system': self.get_system_metrics(),
                'database': self.get_database_metrics(),
                'cache': self.get_cache_metrics(),
                'game': self.get_game_metrics(),
                'services': self.get_service_metrics()
            }
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            return {}

    def get_system_metrics(self) -> Dict:
        """Collect system metrics"""
        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'cpu': {
                    'percent': cpu,
                    'alert': cpu > 80
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'alert': memory.percent > 80
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': disk.percent,
                    'alert': disk.percent > 85
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"System metrics error: {e}")
            return {}

    def get_database_metrics(self) -> Dict:
        """Collect database metrics"""
        try:
            with db.engine.connect() as conn:
                # Get active connections
                result = conn.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                active_connections = result.scalar()

                # Get slow queries
                result = conn.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND now() - query_start > interval '30 seconds'
                """)
                slow_queries = result.scalar()

                return {
                    'connections': {
                        'active': active_connections,
                        'alert': active_connections > 1000
                    },
                    'performance': {
                        'slow_queries': slow_queries,
                        'alert': slow_queries > 0
                    }
                }
        except Exception as e:
            logger.error(f"Database metrics error: {e}")
            return {}

    def get_cache_metrics(self) -> Dict:
        """Collect cache metrics"""
        try:
            info = self.redis.info()
            
            return {
                'memory': {
                    'used': info['used_memory'],
                    'peak': info['used_memory_peak'],
                    'alert': info['used_memory_peak_perc'] > 90
                },
                'connections': {
                    'connected': info['connected_clients'],
                    'rejected': info['rejected_connections'],
                    'alert': info['rejected_connections'] > 0
                },
                'keys': {
                    'total': info['db0']['keys'],
                    'expires': info['db0'].get('expires', 0)
                }
            }
        except Exception as e:
            logger.error(f"Cache metrics error: {e}")
            return {}

    def get_game_metrics(self) -> Dict:
        """Collect game metrics"""
        try:
            active_players = User.query.filter_by(is_online=True).count()
            active_wars = GuildWar.query.filter_by(status='active').count()
            
            return {
                'players': {
                    'active': active_players,
                    'alert': active_players > 10000
                },
                'wars': {
                    'active': active_wars,
                    'alert': active_wars > 100
                }
            }
        except Exception as e:
            logger.error(f"Game metrics error: {e}")
            return {}

    def get_service_metrics(self) -> Dict:
        """Collect service status metrics"""
        services = ['terminusa', 'terminusa-terminal', 'nginx', 'postgresql', 'redis']
        status = {}
        
        for service in services:
            try:
                result = os.system(f'systemctl is-active --quiet {service}')
                status[service] = {
                    'running': result == 0,
                    'alert': result != 0
                }
            except Exception as e:
                logger.error(f"Service check failed for {service}: {e}")
                status[service] = {
                    'running': False,
                    'error': str(e),
                    'alert': True
                }
        
        return status

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        message_str = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )

    async def send_error(self, websocket: WebSocketServerProtocol, message: str):
        """Send error message to client"""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': message
            }))
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    def acknowledge_alert(self, alert_id: str):
        """Update alert acknowledgment status"""
        try:
            with db.session.begin():
                alert = Alert.query.get(alert_id)
                if alert:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.utcnow()
                    db.session.commit()
        except Exception as e:
            logger.error(f"Alert acknowledgment database error: {e}")
            db.session.rollback()
