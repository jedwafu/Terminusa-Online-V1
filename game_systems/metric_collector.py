import asyncio
import json
import logging
import psutil
import redis
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from models import db, User, Guild, GuildWar
from config.monitoring import METRIC_CONFIG

logger = logging.getLogger(__name__)

class MetricCollector:
    def __init__(self, config: Dict, redis_client: redis.Redis):
        self.config = config
        self.redis = redis_client
        self.collection_task = None
        self.aggregation_task = None
        self.last_collection = None
        self.collectors = self.init_collectors()

    def init_collectors(self) -> Dict:
        """Initialize metric collectors"""
        return {
            'system': self.collect_system_metrics,
            'database': self.collect_database_metrics,
            'cache': self.collect_cache_metrics,
            'game': self.collect_game_metrics,
            'network': self.collect_network_metrics,
            'performance': self.collect_performance_metrics
        }

    async def start(self):
        """Start metric collection and aggregation"""
        self.collection_task = asyncio.create_task(self.collect_metrics())
        self.aggregation_task = asyncio.create_task(self.aggregate_metrics())
        logger.info("Metric collector started")

    async def stop(self):
        """Stop metric collection and aggregation"""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        if self.aggregation_task:
            self.aggregation_task.cancel()
            try:
                await self.aggregation_task
            except asyncio.CancelledError:
                pass

        logger.info("Metric collector stopped")

    async def collect_metrics(self):
        """Collect metrics at configured interval"""
        try:
            while True:
                metrics = {}
                
                for name, collector in self.collectors.items():
                    try:
                        metrics[name] = collector()
                    except Exception as e:
                        logger.error(f"Failed to collect {name} metrics: {e}")
                        metrics[name] = {'error': str(e)}

                await self.store_metrics(metrics)
                self.last_collection = datetime.utcnow()
                
                await asyncio.sleep(self.config['collection_interval'])
                
        except asyncio.CancelledError:
            logger.info("Metric collection cancelled")
        except Exception as e:
            logger.error(f"Metric collection error: {e}")

    def collect_system_metrics(self) -> Dict:
        """Collect system resource metrics"""
        cpu = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'total': sum(cpu) / len(cpu),
                'per_cpu': cpu,
                'timestamp': datetime.utcnow().isoformat()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'timestamp': datetime.utcnow().isoformat()
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent,
                'timestamp': datetime.utcnow().isoformat()
            }
        }

    def collect_database_metrics(self) -> Dict:
        """Collect database performance metrics"""
        try:
            with db.engine.connect() as conn:
                # Active connections
                result = conn.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                active_connections = result.scalar()

                # Slow queries
                result = conn.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND now() - query_start > interval '30 seconds'
                """)
                slow_queries = result.scalar()

                # Cache hit ratio
                result = conn.execute("""
                    SELECT 
                        sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) as ratio
                    FROM pg_statio_user_tables
                """)
                cache_hit_ratio = result.scalar() or 0

                return {
                    'connections': active_connections,
                    'slow_queries': slow_queries,
                    'cache_hit_ratio': cache_hit_ratio,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Database metrics collection error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def collect_cache_metrics(self) -> Dict:
        """Collect Redis cache metrics"""
        try:
            info = self.redis.info()
            
            return {
                'memory': {
                    'used': info['used_memory'],
                    'peak': info['used_memory_peak'],
                    'fragmentation': info['mem_fragmentation_ratio']
                },
                'keys': {
                    'total': info['db0']['keys'],
                    'expires': info['db0'].get('expires', 0)
                },
                'operations': {
                    'commands': info['total_commands_processed'],
                    'connections': info['total_connections_received']
                },
                'clients': {
                    'connected': info['connected_clients'],
                    'blocked': info['blocked_clients']
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Cache metrics collection error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def collect_game_metrics(self) -> Dict:
        """Collect game-specific metrics"""
        try:
            active_players = User.query.filter_by(is_online=True).count()
            total_players = User.query.count()
            active_wars = GuildWar.query.filter_by(status='active').count()
            total_wars = GuildWar.query.count()
            active_guilds = Guild.query.filter(Guild.member_count > 0).count()
            
            return {
                'players': {
                    'active': active_players,
                    'total': total_players,
                    'ratio': active_players / total_players if total_players else 0
                },
                'wars': {
                    'active': active_wars,
                    'total': total_wars,
                    'ratio': active_wars / total_wars if total_wars else 0
                },
                'guilds': {
                    'active': active_guilds
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Game metrics collection error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def collect_network_metrics(self) -> Dict:
        """Collect network performance metrics"""
        try:
            network = psutil.net_io_counters()
            
            return {
                'bytes': {
                    'sent': network.bytes_sent,
                    'received': network.bytes_recv
                },
                'packets': {
                    'sent': network.packets_sent,
                    'received': network.packets_recv
                },
                'errors': {
                    'in': network.errin,
                    'out': network.errout
                },
                'drops': {
                    'in': network.dropin,
                    'out': network.dropout
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Network metrics collection error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def collect_performance_metrics(self) -> Dict:
        """Collect application performance metrics"""
        try:
            process = psutil.Process()
            
            return {
                'cpu': {
                    'percent': process.cpu_percent(),
                    'threads': process.num_threads()
                },
                'memory': {
                    'rss': process.memory_info().rss,
                    'vms': process.memory_info().vms
                },
                'io': {
                    'read_count': process.io_counters().read_count,
                    'write_count': process.io_counters().write_count,
                    'read_bytes': process.io_counters().read_bytes,
                    'write_bytes': process.io_counters().write_bytes
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Performance metrics collection error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def store_metrics(self, metrics: Dict):
        """Store collected metrics"""
        try:
            timestamp = datetime.utcnow().isoformat()
            key = f"metrics:{timestamp}"
            
            # Store raw metrics with expiration
            self.redis.setex(
                key,
                self.config['retention_periods']['raw'],
                json.dumps(metrics)
            )
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

    async def aggregate_metrics(self):
        """Aggregate metrics at configured intervals"""
        try:
            while True:
                for window, interval in self.config['aggregation_windows'].items():
                    try:
                        await self.aggregate_window(window, interval)
                    except Exception as e:
                        logger.error(f"Failed to aggregate {window} metrics: {e}")
                
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            logger.info("Metric aggregation cancelled")
        except Exception as e:
            logger.error(f"Metric aggregation error: {e}")

    async def aggregate_window(self, window: str, interval: int):
        """Aggregate metrics for specific time window"""
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=interval)
            
            # Get metrics for window
            metrics = self.get_window_metrics(window_start)
            
            if metrics:
                # Aggregate metrics
                aggregated = self.aggregate_window_metrics(metrics)
                
                # Store aggregated metrics
                timestamp = now.replace(
                    second=0,
                    microsecond=0
                ).isoformat()
                
                key = f"metrics:{window}:{timestamp}"
                self.redis.setex(
                    key,
                    self.config['retention_periods'][window],
                    json.dumps(aggregated)
                )
                
        except Exception as e:
            logger.error(f"Window aggregation error: {e}")

    def get_window_metrics(self, start_time: datetime) -> List[Dict]:
        """Get metrics for time window"""
        try:
            metrics = []
            pattern = f"metrics:{start_time.isoformat()[:13]}*"
            
            for key in self.redis.scan_iter(pattern):
                data = self.redis.get(key)
                if data:
                    metrics.append(json.loads(data))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get window metrics: {e}")
            return []

    def aggregate_window_metrics(self, metrics: List[Dict]) -> Dict:
        """Aggregate metrics for time window"""
        try:
            aggregated = defaultdict(lambda: defaultdict(list))
            
            for metric in metrics:
                for category, data in metric.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, (int, float)):
                                aggregated[category][key].append(value)
            
            # Calculate aggregates
            result = {}
            for category, data in aggregated.items():
                result[category] = {
                    key: {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values)
                    }
                    for key, values in data.items()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Metric aggregation error: {e}")
            return {}

    def get_metrics(self, window: str = 'raw', start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Dict]:
        """Get metrics for time range"""
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=1)
            if not end_time:
                end_time = datetime.utcnow()

            metrics = []
            pattern = f"metrics:{window}:{start_time.isoformat()[:13]}*"
            
            for key in self.redis.scan_iter(pattern):
                timestamp = key.decode().split(':')[2]
                if start_time.isoformat() <= timestamp <= end_time.isoformat():
                    data = self.redis.get(key)
                    if data:
                        metrics.append({
                            'timestamp': timestamp,
                            'data': json.loads(data)
                        })
            
            return sorted(metrics, key=lambda x: x['timestamp'])
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []
