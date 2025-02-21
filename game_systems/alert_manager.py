import logging
import json
import redis
import requests
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from models import db, Alert
from config.monitoring import ALERT_CONFIG, NOTIFICATION_TEMPLATES

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertManager:
    def __init__(self, config: Dict, redis_client: redis.Redis):
        self.config = config
        self.redis = redis_client
        self.alert_task = None
        self.alert_queue = asyncio.Queue()
        
        # Initialize notification channels
        self.init_notification_channels()

    def init_notification_channels(self):
        """Initialize notification channels"""
        self.channels = {
            'email': self.send_email_alert,
            'slack': self.send_slack_alert,
            'websocket': self.send_websocket_alert
        }

    async def start(self):
        """Start alert processing"""
        self.alert_task = asyncio.create_task(self.process_alerts())
        logger.info("Alert manager started")

    async def stop(self):
        """Stop alert processing"""
        if self.alert_task:
            self.alert_task.cancel()
            try:
                await self.alert_task
            except asyncio.CancelledError:
                pass
        logger.info("Alert manager stopped")

    async def process_alerts(self):
        """Process alerts from queue"""
        try:
            while True:
                alert = await self.alert_queue.get()
                
                try:
                    # Store alert in database
                    self.store_alert(alert)
                    
                    # Check alert throttling
                    if not self.is_throttled(alert):
                        # Send notifications
                        await self.send_notifications(alert)
                        
                        # Update alert status
                        self.update_alert_status(alert)
                    
                finally:
                    self.alert_queue.task_done()
                    
        except asyncio.CancelledError:
            logger.info("Alert processing cancelled")
        except Exception as e:
            logger.error(f"Alert processing error: {e}")

    def create_alert(self, title: str, message: str, severity: AlertSeverity, 
                    component: str, details: Dict = None) -> None:
        """Create new alert"""
        try:
            alert = {
                'id': self.generate_alert_id(),
                'title': title,
                'message': message,
                'severity': severity.value,
                'component': component,
                'details': details or {},
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'new'
            }
            
            # Add to processing queue
            self.alert_queue.put_nowait(alert)
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")

    def store_alert(self, alert: Dict) -> None:
        """Store alert in database"""
        try:
            db_alert = Alert(
                alert_id=alert['id'],
                title=alert['title'],
                message=alert['message'],
                severity=alert['severity'],
                component=alert['component'],
                details=json.dumps(alert['details']),
                created_at=datetime.fromisoformat(alert['timestamp'])
            )
            
            db.session.add(db_alert)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
            db.session.rollback()

    def is_throttled(self, alert: Dict) -> bool:
        """Check if alert should be throttled"""
        try:
            throttle_key = f"alert_throttle:{alert['component']}:{alert['severity']}"
            
            # Get throttle window
            window = self.config['throttling'].get(
                alert['severity'],
                self.config['throttling']['default']
            )
            
            # Check if similar alert was sent recently
            if self.redis.get(throttle_key):
                return True
                
            # Set throttle
            self.redis.setex(
                throttle_key,
                window,
                alert['id']
            )
            
            return False
            
        except Exception as e:
            logger.error(f"Throttle check failed: {e}")
            return False

    async def send_notifications(self, alert: Dict) -> None:
        """Send alert notifications through configured channels"""
        try:
            tasks = []
            
            for channel, config in self.config['channels'].items():
                if not config['enabled']:
                    continue
                    
                if not self.should_notify(alert, config['min_severity']):
                    continue
                    
                send_func = self.channels.get(channel)
                if send_func:
                    tasks.append(
                        asyncio.create_task(send_func(alert))
                    )
            
            if tasks:
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")

    async def send_email_alert(self, alert: Dict) -> None:
        """Send alert via email"""
        try:
            template = NOTIFICATION_TEMPLATES['alert']['email']
            recipients = self.config['channels']['email']['recipients']
            
            msg = MIMEMultipart()
            msg['Subject'] = template['subject'].format(**alert)
            msg['From'] = 'monitoring@terminusa.online'
            msg['To'] = ', '.join(recipients)
            
            body = template['body'].format(**alert)
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT'))) as server:
                server.starttls()
                server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def send_slack_alert(self, alert: Dict) -> None:
        """Send alert via Slack"""
        try:
            template = NOTIFICATION_TEMPLATES['alert']['slack']
            webhook_url = self.config['channels']['slack']['webhook_url']
            
            message = {
                'text': template['title'].format(**alert),
                'attachments': [{
                    'color': self.get_slack_color(alert['severity']),
                    'fields': [
                        {
                            'title': field,
                            'value': str(alert.get(field.lower(), 'N/A')),
                            'short': True
                        }
                        for field in template['fields']
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status != 200:
                        logger.error(f"Slack API error: {await response.text()}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def send_websocket_alert(self, alert: Dict) -> None:
        """Send alert via WebSocket"""
        try:
            from game_systems.monitoring_websocket import monitoring_websocket
            
            if monitoring_websocket:
                await monitoring_websocket.broadcast({
                    'type': 'alert',
                    'data': alert
                })
                
        except Exception as e:
            logger.error(f"Failed to send WebSocket alert: {e}")

    def update_alert_status(self, alert: Dict) -> None:
        """Update alert status after notification"""
        try:
            db_alert = Alert.query.filter_by(alert_id=alert['id']).first()
            if db_alert:
                db_alert.status = 'notified'
                db_alert.notified_at = datetime.utcnow()
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            db.session.rollback()

    def should_notify(self, alert: Dict, min_severity: str) -> bool:
        """Check if alert meets minimum severity for notification"""
        severity_levels = {
            'info': 0,
            'warning': 1,
            'critical': 2
        }
        
        alert_level = severity_levels.get(alert['severity'], 0)
        min_level = severity_levels.get(min_severity, 0)
        
        return alert_level >= min_level

    def get_slack_color(self, severity: str) -> str:
        """Get Slack attachment color for severity"""
        colors = {
            'info': '#2196F3',
            'warning': '#FFC107',
            'critical': '#F44336'
        }
        return colors.get(severity, '#757575')

    def generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{id(self)}"

    def get_pending_count(self) -> int:
        """Get count of pending alerts"""
        try:
            return Alert.query.filter_by(status='new').count()
        except Exception as e:
            logger.error(f"Failed to get pending alert count: {e}")
            return 0

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            alerts = Alert.query.filter(
                Alert.created_at >= since
            ).order_by(Alert.created_at.desc()).all()
            
            return [alert.to_dict() for alert in alerts]
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            alert = Alert.query.filter_by(alert_id=alert_id).first()
            if alert:
                alert.status = 'acknowledged'
                alert.acknowledged_at = datetime.utcnow()
                db.session.commit()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            db.session.rollback()
            return False
