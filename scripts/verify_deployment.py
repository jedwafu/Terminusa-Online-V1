#!/usr/bin/env python3
import requests
import psycopg2
import redis
import websockets
import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('deployment_verification')

class DeploymentVerifier:
    def __init__(self):
        self.config = {
            'urls': {
                'main': 'https://terminusa.online',
                'game': 'https://play.terminusa.online',
                'websocket': 'wss://play.terminusa.online/ws'
            },
            'endpoints': [
                '/health',
                '/api/status',
                '/api/version',
                '/static/css/style.css',
                '/static/js/main.js'
            ],
            'db_tables': [
                'user',
                'character',
                'guild',
                'guild_war',
                'territory',
                'currency',
                'inventory',
                'transaction'
            ]
        }

    async def verify_all(self) -> bool:
        """Run all verification checks"""
        try:
            checks = [
                self.verify_web_services(),
                self.verify_database(),
                self.verify_cache(),
                self.verify_static_files(),
                self.verify_websocket(),
                self.verify_game_systems(),
                self.verify_services()
            ]

            results = await asyncio.gather(*checks)
            success = all(results)

            if success:
                logger.info("✅ All deployment verification checks passed")
            else:
                logger.error("❌ Some deployment verification checks failed")

            return success

        except Exception as e:
            logger.error(f"Deployment verification failed: {e}")
            return False

    async def verify_web_services(self) -> bool:
        """Verify web services are responding correctly"""
        try:
            for service, base_url in self.config['urls'].items():
                if service == 'websocket':
                    continue

                for endpoint in self.config['endpoints']:
                    url = f"{base_url}{endpoint}"
                    response = requests.get(url)
                    
                    if response.status_code != 200:
                        logger.error(f"❌ {url} returned status {response.status_code}")
                        return False
                    
                    logger.info(f"✅ {url} is responding correctly")

            return True

        except Exception as e:
            logger.error(f"Web services verification failed: {e}")
            return False

    async def verify_database(self) -> bool:
        """Verify database connection and tables"""
        try:
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST')
            )
            cursor = conn.cursor()

            # Check tables exist
            for table in self.config['db_tables']:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
                exists = cursor.fetchone()[0]
                
                if not exists:
                    logger.error(f"❌ Table '{table}' not found in database")
                    return False
                
                logger.info(f"✅ Table '{table}' exists")

            # Check migrations
            cursor.execute("SELECT version_num FROM alembic_version")
            current_version = cursor.fetchone()[0]
            logger.info(f"✅ Database migration version: {current_version}")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False

    async def verify_cache(self) -> bool:
        """Verify Redis cache is working"""
        try:
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0
            )

            # Test cache operations
            test_key = 'deployment_test'
            test_value = 'verification'
            
            redis_client.set(test_key, test_value)
            result = redis_client.get(test_key)
            redis_client.delete(test_key)

            if result.decode() != test_value:
                logger.error("❌ Cache read/write test failed")
                return False

            logger.info("✅ Cache operations working correctly")
            return True

        except Exception as e:
            logger.error(f"Cache verification failed: {e}")
            return False

    async def verify_static_files(self) -> bool:
        """Verify static files are served correctly"""
        try:
            static_files = [
                '/static/css/style.css',
                '/static/css/territory_map.css',
                '/static/js/territory_map.js',
                '/static/js/territory_actions.js'
            ]

            for file_path in static_files:
                response = requests.get(f"{self.config['urls']['main']}{file_path}")
                
                if response.status_code != 200:
                    logger.error(f"❌ Static file {file_path} not found")
                    return False
                
                logger.info(f"✅ Static file {file_path} is accessible")

            return True

        except Exception as e:
            logger.error(f"Static files verification failed: {e}")
            return False

    async def verify_websocket(self) -> bool:
        """Verify WebSocket connection"""
        try:
            async with websockets.connect(self.config['urls']['websocket']) as websocket:
                # Send test message
                await websocket.send(json.dumps({
                    'type': 'ping',
                    'timestamp': datetime.now().isoformat()
                }))

                # Wait for response
                response = await websocket.recv()
                data = json.loads(response)

                if data.get('type') != 'pong':
                    logger.error("❌ WebSocket ping test failed")
                    return False

                logger.info("✅ WebSocket connection working")
                return True

        except Exception as e:
            logger.error(f"WebSocket verification failed: {e}")
            return False

    async def verify_game_systems(self) -> bool:
        """Verify game systems are operational"""
        try:
            systems = [
                'territory',
                'guild_war',
                'marketplace',
                'currency',
                'achievement'
            ]

            for system in systems:
                response = requests.get(
                    f"{self.config['urls']['game']}/api/system/{system}/status"
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Game system '{system}' check failed")
                    return False
                
                logger.info(f"✅ Game system '{system}' is operational")

            return True

        except Exception as e:
            logger.error(f"Game systems verification failed: {e}")
            return False

    async def verify_services(self) -> bool:
        """Verify system services are running"""
        try:
            services = [
                'terminusa',
                'terminusa-terminal',
                'nginx',
                'postgresql',
                'redis'
            ]

            for service in services:
                result = os.system(f'systemctl is-active --quiet {service}')
                
                if result != 0:
                    logger.error(f"❌ Service '{service}' is not running")
                    return False
                
                logger.info(f"✅ Service '{service}' is running")

            return True

        except Exception as e:
            logger.error(f"Services verification failed: {e}")
            return False

    def generate_report(self) -> str:
        """Generate deployment verification report"""
        report = [
            "=== Deployment Verification Report ===",
            f"Timestamp: {datetime.now().isoformat()}",
            f"Environment: {os.getenv('FLASK_ENV', 'production')}",
            "",
            "Web Services:",
            "  Main Website: ✅" if self.verify_web_services() else "  Main Website: ❌",
            "  Game Server: ✅" if self.verify_game_systems() else "  Game Server: ❌",
            "",
            "Database:",
            "  Connection: ✅" if self.verify_database() else "  Connection: ❌",
            "",
            "Cache:",
            "  Redis: ✅" if self.verify_cache() else "  Redis: ❌",
            "",
            "WebSocket:",
            "  Connection: ✅" if self.verify_websocket() else "  Connection: ❌",
            "",
            "Services:",
            "  Status: ✅" if self.verify_services() else "  Status: ❌",
            "",
            "=== End Report ==="
        ]

        return "\n".join(report)

def main():
    verifier = DeploymentVerifier()
    
    try:
        success = asyncio.run(verifier.verify_all())
        report = verifier.generate_report()
        
        print("\n" + report + "\n")
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Verification script failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
