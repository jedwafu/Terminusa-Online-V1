#!/usr/bin/env python3
import psutil
import requests
import json
import time
import logging
import os
import redis
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/terminusa/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('system_monitor')

class SystemMonitor:
    def __init__(self):
        self.config = {
            'urls': {
                'main': 'https://terminusa.online',
                'game': 'https://play.terminusa.online',
                'health': '/health',
                'metrics': '/metrics'
            },
            'thresholds': {
                'cpu_percent': 80,
                'memory_percent': 80,
                'disk_percent': 85,
                'response_time': 2,
                'connection_limit': 1000
            },
            'intervals': {
                'system': 60,
                'application': 30,
                'database': 300,
                'alert': 1800
            }
        }
        
        # Initialize connections
        self.init_connections()

    def init_connections(self):
        """Initialize database and cache connections"""
        try:
            self.db = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST')
            )
            
            self.redis = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise

    def check_system_resources(self) -> Dict:
        """Monitor system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'alert': cpu_percent > self.config['thresholds']['cpu_percent']
                },
                'memory': {
                    'percent': memory.percent,
                    'available': memory.available,
                    'alert': memory.percent > self.config['thresholds']['memory_percent']
                },
                'disk': {
                    'percent': disk.percent,
                    'free': disk.free,
                    'alert': disk.percent > self.config['thresholds']['disk_percent']
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {}

    def check_application_health(self) -> Dict:
        """Monitor application endpoints"""
        results = {}
        
        for service, base_url in self.config['urls'].items():
            if service in ['health', 'metrics']:
                continue
                
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{self.config['urls']['health']}")
                response_time = time.time() - start_time
                
                results[service] = {
                    'status': response.status_code == 200,
                    'response_time': response_time,
                    'alert': response_time > self.config['thresholds']['response_time']
                }
                
            except Exception as e:
                logger.error(f"Health check failed for {service}: {e}")
                results[service] = {
                    'status': False,
                    'error': str(e),
                    'alert': True
                }
        
        return results

    def check_database_health(self) -> Dict:
        """Monitor database health"""
        try:
            cursor = self.db.cursor()
            
            # Check connections
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            
            # Check slow queries
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE state = 'active' 
                AND now() - query_start > interval '30 seconds'
            """)
            slow_queries = cursor.fetchone()[0]
            
            # Check cache hit ratio
            cursor.execute("""
                SELECT 
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            cache_hit_ratio = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'connections': {
                    'active': active_connections,
                    'alert': active_connections > self.config['thresholds']['connection_limit']
                },
                'performance': {
                    'slow_queries': slow_queries,
                    'cache_hit_ratio': cache_hit_ratio,
                    'alert': slow_queries > 0 or cache_hit_ratio < 0.95
                }
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {}

    def check_cache_health(self) -> Dict:
        """Monitor Redis cache health"""
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
            logger.error(f"Cache health check failed: {e}")
            return {}

    def check_service_status(self) -> Dict:
        """Check status of system services"""
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

    def generate_alert(self, check_type: str, data: Dict) -> None:
        """Generate alerts for critical issues"""
        alerts = []
        
        for category, metrics in data.items():
            if isinstance(metrics, dict) and metrics.get('alert'):
                alerts.append(f"{check_type.upper()} ALERT: {category}")
                
        if alerts:
            alert_msg = "\n".join(alerts)
            logger.warning(alert_msg)
            
            # Send alert (implement your preferred notification method)
            self.send_alert(alert_msg)

    def send_alert(self, message: str) -> None:
        """Send alert through configured channels"""
        # Example: Send to admin email
        try:
            requests.post(
                'https://terminusa.online/api/admin/alert',
                json={
                    'message': message,
                    'timestamp': datetime.now().isoformat(),
                    'level': 'warning'
                },
                headers={'Authorization': f"Bearer {os.getenv('ADMIN_API_KEY')}"}
            )
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def run_monitoring(self):
        """Main monitoring loop"""
        while True:
            try:
                # System resources
                if time.time() % self.config['intervals']['system'] == 0:
                    system_data = self.check_system_resources()
                    self.generate_alert('system', system_data)
                
                # Application health
                if time.time() % self.config['intervals']['application'] == 0:
                    app_data = self.check_application_health()
                    self.generate_alert('application', app_data)
                
                # Database health
                if time.time() % self.config['intervals']['database'] == 0:
                    db_data = self.check_database_health()
                    cache_data = self.check_cache_health()
                    service_data = self.check_service_status()
                    
                    self.generate_alert('database', db_data)
                    self.generate_alert('cache', cache_data)
                    self.generate_alert('service', service_data)
                
                # Store metrics
                self.store_metrics({
                    'system': system_data,
                    'application': app_data,
                    'database': db_data,
                    'cache': cache_data,
                    'services': service_data
                })
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}")
                time.sleep(10)

    def store_metrics(self, metrics: Dict) -> None:
        """Store metrics for historical analysis"""
        try:
            timestamp = datetime.now().isoformat()
            self.redis.setex(
                f"metrics:{timestamp}",
                86400,  # Store for 24 hours
                json.dumps(metrics)
            )
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

if __name__ == '__main__':
    monitor = SystemMonitor()
    monitor.run_monitoring()
