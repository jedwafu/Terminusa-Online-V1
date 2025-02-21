from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from datetime import datetime, timedelta
import psutil
import redis
import os
from functools import wraps

from models import db, User, Guild, GuildWar, Alert
from game_systems.monitoring_websocket import MonitoringWebSocket

monitoring_bp = Blueprint('monitoring', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {os.getenv('ADMIN_API_KEY')}":
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@monitoring_bp.route('/api/monitoring/metrics')
@admin_required
def get_metrics():
    """Get current system metrics"""
    try:
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'system': get_system_metrics(),
                'database': get_database_metrics(),
                'cache': get_cache_metrics(),
                'game': get_game_metrics(),
                'services': get_service_status()
            }
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitoring_bp.route('/api/monitoring/alerts')
@admin_required
def get_alerts():
    """Get recent alerts"""
    try:
        # Get alerts from last 24 hours
        since = datetime.utcnow() - timedelta(days=1)
        alerts = Alert.query.filter(
            Alert.created_at >= since
        ).order_by(Alert.created_at.desc()).all()

        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitoring_bp.route('/api/monitoring/alerts/<alert_id>/acknowledge', methods=['POST'])
@admin_required
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({
                'success': False,
                'error': 'Alert not found'
            }), 404

        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Alert acknowledged'
        })
    except Exception as e:
        current_app.logger.error(f"Failed to acknowledge alert: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitoring_bp.route('/api/monitoring/logs')
@admin_required
def get_logs():
    """Get recent system logs"""
    try:
        level = request.args.get('level', 'all')
        limit = int(request.args.get('limit', 100))
        
        # Read logs from file
        logs = read_system_logs(level, limit)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitoring_bp.route('/api/monitoring/performance')
@admin_required
def get_performance():
    """Get detailed performance metrics"""
    try:
        period = request.args.get('period', '1h')  # 1h, 24h, 7d
        metrics = get_historical_metrics(period)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get performance metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitoring_bp.route('/api/monitoring/services')
@admin_required
def get_services():
    """Get service status information"""
    try:
        return jsonify({
            'success': True,
            'services': get_service_status()
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get service status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitoring_bp.route('/api/monitoring/backup/status')
@admin_required
def get_backup_status():
    """Get backup system status"""
    try:
        return jsonify({
            'success': True,
            'backup': get_backup_info()
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get backup status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_system_metrics():
    """Collect system resource metrics"""
    cpu = psutil.cpu_percent(interval=1)
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

def get_database_metrics():
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
        current_app.logger.error(f"Database metrics error: {e}")
        return {}

def get_cache_metrics():
    """Collect cache metrics"""
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0
        )
        info = redis_client.info()
        
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
        current_app.logger.error(f"Cache metrics error: {e}")
        return {}

def get_game_metrics():
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
        current_app.logger.error(f"Game metrics error: {e}")
        return {}

def get_service_status():
    """Get service status information"""
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
            current_app.logger.error(f"Service check failed for {service}: {e}")
            status[service] = {
                'running': False,
                'error': str(e),
                'alert': True
            }
    
    return status

def read_system_logs(level='all', limit=100):
    """Read system logs"""
    try:
        logs = []
        log_file = '/var/log/terminusa/app.log'
        
        with open(log_file, 'r') as f:
            for line in f.readlines()[-limit:]:
                log_level = get_log_level(line)
                if level == 'all' or log_level == level:
                    logs.append(parse_log_line(line))
        
        return logs
    except Exception as e:
        current_app.logger.error(f"Log reading error: {e}")
        return []

def get_log_level(line):
    """Extract log level from log line"""
    if 'ERROR' in line:
        return 'error'
    elif 'WARNING' in line:
        return 'warning'
    elif 'INFO' in line:
        return 'info'
    return 'debug'

def parse_log_line(line):
    """Parse log line into structured format"""
    try:
        parts = line.split(' - ')
        return {
            'timestamp': parts[0],
            'level': get_log_level(parts[1]),
            'message': ' - '.join(parts[2:]).strip()
        }
    except Exception:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'error',
            'message': line.strip()
        }

def get_historical_metrics(period):
    """Get historical metrics from Redis"""
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0
        )
        
        # Get metrics keys for period
        since = get_period_timestamp(period)
        keys = redis_client.keys('metrics:*')
        metrics = []
        
        for key in sorted(keys):
            timestamp = key.decode().split(':')[1]
            if timestamp >= since:
                data = redis_client.get(key)
                if data:
                    metrics.append({
                        'timestamp': timestamp,
                        'data': json.loads(data)
                    })
        
        return metrics
    except Exception as e:
        current_app.logger.error(f"Historical metrics error: {e}")
        return []

def get_period_timestamp(period):
    """Get timestamp for start of period"""
    now = datetime.utcnow()
    if period == '1h':
        return (now - timedelta(hours=1)).isoformat()
    elif period == '24h':
        return (now - timedelta(days=1)).isoformat()
    elif period == '7d':
        return (now - timedelta(days=7)).isoformat()
    return now.isoformat()

def get_backup_info():
    """Get backup system information"""
    try:
        backup_dir = '/var/www/backups'
        backups = []
        
        for file in os.listdir(backup_dir):
            if file.endswith('.tar.gz'):
                path = os.path.join(backup_dir, file)
                stat = os.stat(path)
                backups.append({
                    'name': file,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        return {
            'last_backup': max(backups, key=lambda x: x['created_at']) if backups else None,
            'total_backups': len(backups),
            'total_size': sum(b['size'] for b in backups)
        }
    except Exception as e:
        current_app.logger.error(f"Backup info error: {e}")
        return {}
