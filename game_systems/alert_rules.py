import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from models import db, Alert, User, Guild, GuildWar
from config.monitoring import SYSTEM_THRESHOLDS, DATABASE_THRESHOLDS, GAME_THRESHOLDS
from game_systems.alert_manager import AlertManager, AlertSeverity

logger = logging.getLogger(__name__)

class AlertCategory(Enum):
    SYSTEM = "system"
    DATABASE = "database"
    GAME = "game"
    SECURITY = "security"
    PERFORMANCE = "performance"

class AlertRules:
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.last_check = {}

    async def check_all_rules(self, metrics: Dict):
        """Check all alert rules against current metrics"""
        try:
            await self.check_system_rules(metrics.get('system', {}))
            await self.check_database_rules(metrics.get('database', {}))
            await self.check_game_rules(metrics.get('game', {}))
            await self.check_security_rules(metrics.get('security', {}))
            await self.check_performance_rules(metrics.get('performance', {}))
            
        except Exception as e:
            logger.error(f"Failed to check alert rules: {e}")

    async def check_system_rules(self, metrics: Dict):
        """Check system resource alert rules"""
        try:
            # CPU Usage
            if metrics.get('cpu', {}).get('percent', 0) > SYSTEM_THRESHOLDS['cpu']['critical']:
                await self.create_alert(
                    "High CPU Usage",
                    f"CPU usage is at {metrics['cpu']['percent']}%",
                    AlertSeverity.CRITICAL,
                    AlertCategory.SYSTEM,
                    metrics['cpu']
                )
            elif metrics.get('cpu', {}).get('percent', 0) > SYSTEM_THRESHOLDS['cpu']['warning']:
                await self.create_alert(
                    "Elevated CPU Usage",
                    f"CPU usage is at {metrics['cpu']['percent']}%",
                    AlertSeverity.WARNING,
                    AlertCategory.SYSTEM,
                    metrics['cpu']
                )

            # Memory Usage
            if metrics.get('memory', {}).get('percent', 0) > SYSTEM_THRESHOLDS['memory']['critical']:
                await self.create_alert(
                    "High Memory Usage",
                    f"Memory usage is at {metrics['memory']['percent']}%",
                    AlertSeverity.CRITICAL,
                    AlertCategory.SYSTEM,
                    metrics['memory']
                )
            elif metrics.get('memory', {}).get('percent', 0) > SYSTEM_THRESHOLDS['memory']['warning']:
                await self.create_alert(
                    "Elevated Memory Usage",
                    f"Memory usage is at {metrics['memory']['percent']}%",
                    AlertSeverity.WARNING,
                    AlertCategory.SYSTEM,
                    metrics['memory']
                )

            # Disk Usage
            if metrics.get('disk', {}).get('percent', 0) > SYSTEM_THRESHOLDS['disk']['critical']:
                await self.create_alert(
                    "Critical Disk Space",
                    f"Disk usage is at {metrics['disk']['percent']}%",
                    AlertSeverity.CRITICAL,
                    AlertCategory.SYSTEM,
                    metrics['disk']
                )
            elif metrics.get('disk', {}).get('percent', 0) > SYSTEM_THRESHOLDS['disk']['warning']:
                await self.create_alert(
                    "Low Disk Space",
                    f"Disk usage is at {metrics['disk']['percent']}%",
                    AlertSeverity.WARNING,
                    AlertCategory.SYSTEM,
                    metrics['disk']
                )

        except Exception as e:
            logger.error(f"Failed to check system rules: {e}")

    async def check_database_rules(self, metrics: Dict):
        """Check database performance alert rules"""
        try:
            # Connection Count
            if metrics.get('connections', {}).get('active', 0) > DATABASE_THRESHOLDS['connections']['critical']:
                await self.create_alert(
                    "High Database Connections",
                    f"Active connections: {metrics['connections']['active']}",
                    AlertSeverity.CRITICAL,
                    AlertCategory.DATABASE,
                    metrics['connections']
                )
            elif metrics.get('connections', {}).get('active', 0) > DATABASE_THRESHOLDS['connections']['warning']:
                await self.create_alert(
                    "Elevated Database Connections",
                    f"Active connections: {metrics['connections']['active']}",
                    AlertSeverity.WARNING,
                    AlertCategory.DATABASE,
                    metrics['connections']
                )

            # Slow Queries
            if metrics.get('performance', {}).get('slow_queries', 0) > 0:
                await self.create_alert(
                    "Slow Database Queries Detected",
                    f"Number of slow queries: {metrics['performance']['slow_queries']}",
                    AlertSeverity.WARNING,
                    AlertCategory.DATABASE,
                    metrics['performance']
                )

            # Cache Hit Ratio
            if metrics.get('performance', {}).get('cache_hit_ratio', 1) < DATABASE_THRESHOLDS['cache_hit_ratio']['critical']:
                await self.create_alert(
                    "Low Cache Hit Ratio",
                    f"Cache hit ratio: {metrics['performance']['cache_hit_ratio']:.2%}",
                    AlertSeverity.WARNING,
                    AlertCategory.DATABASE,
                    metrics['performance']
                )

        except Exception as e:
            logger.error(f"Failed to check database rules: {e}")

    async def check_game_rules(self, metrics: Dict):
        """Check game-specific alert rules"""
        try:
            # Active Players
            if metrics.get('players', {}).get('active', 0) > GAME_THRESHOLDS['active_players']['critical']:
                await self.create_alert(
                    "High Player Count",
                    f"Active players: {metrics['players']['active']}",
                    AlertSeverity.WARNING,
                    AlertCategory.GAME,
                    metrics['players']
                )

            # Active Wars
            if metrics.get('wars', {}).get('active', 0) > GAME_THRESHOLDS['active_wars']['critical']:
                await self.create_alert(
                    "High Number of Active Wars",
                    f"Active wars: {metrics['wars']['active']}",
                    AlertSeverity.WARNING,
                    AlertCategory.GAME,
                    metrics['wars']
                )

            # Transaction Rate
            if metrics.get('transactions', {}).get('rate', 0) > GAME_THRESHOLDS['transaction_rate']['critical']:
                await self.create_alert(
                    "High Transaction Rate",
                    f"Transactions per minute: {metrics['transactions']['rate']}",
                    AlertSeverity.WARNING,
                    AlertCategory.GAME,
                    metrics['transactions']
                )

            # Response Time
            if metrics.get('performance', {}).get('response_time', 0) > GAME_THRESHOLDS['response_time']['critical']:
                await self.create_alert(
                    "High Response Time",
                    f"Average response time: {metrics['performance']['response_time']}ms",
                    AlertSeverity.CRITICAL,
                    AlertCategory.GAME,
                    metrics['performance']
                )

        except Exception as e:
            logger.error(f"Failed to check game rules: {e}")

    async def check_security_rules(self, metrics: Dict):
        """Check security-related alert rules"""
        try:
            # Failed Logins
            if metrics.get('security', {}).get('failed_logins', 0) > GAME_THRESHOLDS['security']['failed_login_threshold']:
                await self.create_alert(
                    "High Failed Login Attempts",
                    f"Failed logins in last hour: {metrics['security']['failed_logins']}",
                    AlertSeverity.WARNING,
                    AlertCategory.SECURITY,
                    metrics['security']
                )

            # Suspicious IPs
            if metrics.get('security', {}).get('suspicious_ips', 0) > GAME_THRESHOLDS['security']['suspicious_ip_threshold']:
                await self.create_alert(
                    "High Number of Suspicious IPs",
                    f"Suspicious IPs detected: {metrics['security']['suspicious_ips']}",
                    AlertSeverity.WARNING,
                    AlertCategory.SECURITY,
                    metrics['security']
                )

        except Exception as e:
            logger.error(f"Failed to check security rules: {e}")

    async def check_performance_rules(self, metrics: Dict):
        """Check performance-related alert rules"""
        try:
            # Memory Leaks
            if self.detect_memory_leak(metrics.get('memory', {})):
                await self.create_alert(
                    "Potential Memory Leak Detected",
                    "Memory usage showing consistent increase",
                    AlertSeverity.WARNING,
                    AlertCategory.PERFORMANCE,
                    metrics['memory']
                )

            # Resource Usage
            for process, usage in metrics.get('processes', {}).items():
                if usage.get('cpu', 0) > GAME_THRESHOLDS['performance']['process_cpu_threshold']:
                    await self.create_alert(
                        f"High CPU Usage by Process",
                        f"Process {process} CPU usage: {usage['cpu']}%",
                        AlertSeverity.WARNING,
                        AlertCategory.PERFORMANCE,
                        usage
                    )

        except Exception as e:
            logger.error(f"Failed to check performance rules: {e}")

    def detect_memory_leak(self, memory_metrics: Dict) -> bool:
        """Detect potential memory leaks"""
        try:
            if not memory_metrics:
                return False

            # Get historical memory usage
            history = self.get_metric_history('memory.used', hours=6)
            if len(history) < 10:
                return False

            # Check for consistent increase
            increases = 0
            for i in range(1, len(history)):
                if history[i] > history[i-1]:
                    increases += 1

            # If more than 90% of samples show increase, potential leak
            return (increases / len(history)) > 0.9

        except Exception as e:
            logger.error(f"Failed to detect memory leak: {e}")
            return False

    def get_metric_history(self, metric_path: str, hours: int = 1) -> List[float]:
        """Get historical values for a metric"""
        try:
            values = []
            now = datetime.utcnow()
            start_time = now - timedelta(hours=hours)

            # Get metrics from Redis
            pattern = f"metrics:*"
            for key in self.alert_manager.redis.scan_iter(pattern):
                timestamp = key.decode().split(':')[1]
                if datetime.fromisoformat(timestamp) >= start_time:
                    data = self.alert_manager.redis.get(key)
                    if data:
                        metric_data = json.loads(data)
                        value = self.get_nested_value(metric_data, metric_path)
                        if value is not None:
                            values.append(value)

            return sorted(values)

        except Exception as e:
            logger.error(f"Failed to get metric history: {e}")
            return []

    def get_nested_value(self, data: Dict, path: str) -> Optional[float]:
        """Get value from nested dictionary using dot notation"""
        try:
            for key in path.split('.'):
                data = data[key]
            return float(data) if data is not None else None
        except (KeyError, ValueError, TypeError):
            return None

    async def create_alert(self, title: str, message: str, severity: AlertSeverity,
                          category: AlertCategory, details: Dict = None):
        """Create new alert if not throttled"""
        try:
            # Check if similar alert was created recently
            alert_key = f"{category.value}:{title}"
            if self.is_alert_throttled(alert_key):
                return

            # Create alert
            await self.alert_manager.create_alert(
                title=title,
                message=message,
                severity=severity,
                component=category.value,
                details=details or {}
            )

            # Update last check time
            self.last_check[alert_key] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")

    def is_alert_throttled(self, alert_key: str) -> bool:
        """Check if alert should be throttled"""
        try:
            last_time = self.last_check.get(alert_key)
            if not last_time:
                return False

            # Get throttle window from config
            window = self.alert_manager.config['throttling'].get(
                'default',
                300  # 5 minutes default
            )

            return (datetime.utcnow() - last_time).total_seconds() < window

        except Exception as e:
            logger.error(f"Failed to check alert throttling: {e}")
            return False
