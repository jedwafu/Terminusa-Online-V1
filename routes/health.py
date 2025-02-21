from flask import Blueprint, jsonify, current_app
from datetime import datetime
import psutil
import redis
import psycopg2
import os
from functools import wraps

health_bp = Blueprint('health', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {os.getenv('ADMIN_API_KEY')}":
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@health_bp.route('/health')
def basic_health():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': current_app.config.get('VERSION')
    })

@health_bp.route('/health/detailed')
@admin_required
def detailed_health():
    """Detailed system health information"""
    try:
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'version': current_app.config.get('VERSION'),
            'system': get_system_health(),
            'database': get_database_health(),
            'cache': get_cache_health(),
            'services': get_service_health(),
            'game': get_game_health()
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@health_bp.route('/health/system')
@admin_required
def system_health():
    """System resource health information"""
    try:
        return jsonify(get_system_health())
    except Exception as e:
        current_app.logger.error(f"System health check failed: {e}")
        return jsonify({'error': str(e)}), 500

@health_bp.route('/health/database')
@admin_required
def database_health():
    """Database health information"""
    try:
        return jsonify(get_database_health())
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}")
        return jsonify({'error': str(e)}), 500

@health_bp.route('/health/cache')
@admin_required
def cache_health():
    """Cache health information"""
    try:
        return jsonify(get_cache_health())
    except Exception as e:
        current_app.logger.error(f"Cache health check failed: {e}")
        return jsonify({'error': str(e)}), 500

@health_bp.route('/health/services')
@admin_required
def service_health():
    """Service status information"""
    try:
        return jsonify(get_service_health())
    except Exception as e:
        current_app.logger.error(f"Service health check failed: {e}")
        return jsonify({'error': str(e)}), 500

@health_bp.route('/health/game')
@admin_required
def game_health():
    """Game systems health information"""
    try:
        return jsonify(get_game_health())
    except Exception as e:
        current_app.logger.error(f"Game health check failed: {e}")
        return jsonify({'error': str(e)}), 500

def get_system_health():
    """Get system resource information"""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
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
        }
    }

def get_database_health():
    """Get database health information"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST')
        )
        cursor = conn.cursor()

        # Check active connections
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
        conn.close()

        return {
            'status': 'ok',
            'connections': {
                'active': active_connections,
                'alert': active_connections > 1000
            },
            'performance': {
                'slow_queries': slow_queries,
                'cache_hit_ratio': cache_hit_ratio,
                'alert': slow_queries > 0 or cache_hit_ratio < 0.95
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_cache_health():
    """Get cache health information"""
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0
        )
        
        info = redis_client.info()
        
        return {
            'status': 'ok',
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
        return {
            'status': 'error',
            'error': str(e)
        }

def get_service_health():
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
            status[service] = {
                'running': False,
                'error': str(e),
                'alert': True
            }
    
    return status

def get_game_health():
    """Get game systems health information"""
    from game_systems.territory_control import TerritoryControl
    from game_systems.guild_war import GuildWar
    from game_systems.currency_system import CurrencySystem
    
    try:
        # Get active wars
        active_wars = GuildWar.query.filter_by(status='active').count()
        
        # Get territory stats
        territory_stats = TerritoryControl.get_statistics()
        
        # Get currency stats
        currency_stats = CurrencySystem.get_statistics()
        
        return {
            'status': 'ok',
            'active_wars': active_wars,
            'territories': territory_stats,
            'currencies': currency_stats,
            'alerts': {
                'wars': active_wars > 100,
                'territories': territory_stats.get('alert', False),
                'currencies': currency_stats.get('alert', False)
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
