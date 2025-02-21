import logging
import json
import smtplib
import aiohttp
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Template

from config.monitoring import ALERT_CONFIG
from models import db, Alert

logger = logging.getLogger(__name__)

class NotificationHandler:
    def __init__(self):
        self.email_templates = self.load_email_templates()
        self.slack_templates = self.load_slack_templates()
        self.dashboard_url = "https://terminusa.online/admin/monitoring"

    def load_email_templates(self) -> Dict[str, Template]:
        """Load email templates"""
        try:
            templates = {}
            with open('templates/alerts/email_templates.html', 'r') as f:
                content = f.read()
                
            # Extract templates from script tags
            for severity in ['critical', 'warning', 'info']:
                start_tag = f'<script type="text/template" id="{severity}-alert">'
                end_tag = '</script>'
                start_idx = content.find(start_tag) + len(start_tag)
                end_idx = content.find(end_tag, start_idx)
                
                if start_idx > 0 and end_idx > 0:
                    template_content = content[start_idx:end_idx].strip()
                    templates[severity] = Template(template_content)
                    
            return templates
            
        except Exception as e:
            logger.error(f"Failed to load email templates: {e}")
            return {}

    def load_slack_templates(self) -> Dict:
        """Load Slack templates"""
        try:
            with open('templates/alerts/slack_templates.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Slack templates: {e}")
            return {}

    async def send_notifications(self, alert: Dict):
        """Send notifications through configured channels"""
        try:
            tasks = []
            
            for channel, config in ALERT_CONFIG['channels'].items():
                if not config['enabled']:
                    continue
                    
                if not self.should_notify(alert, config['min_severity']):
                    continue
                    
                if channel == 'email':
                    tasks.append(self.send_email_alert(alert))
                elif channel == 'slack':
                    tasks.append(self.send_slack_alert(alert))
                elif channel == 'websocket':
                    tasks.append(self.send_websocket_alert(alert))
            
            if tasks:
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")

    async def send_email_alert(self, alert: Dict):
        """Send alert via email"""
        try:
            template = self.email_templates.get(alert['severity'])
            if not template:
                logger.error(f"Email template not found for severity: {alert['severity']}")
                return

            # Prepare email content
            content = template.render(
                title=alert['title'],
                message=alert['message'],
                timestamp=alert['timestamp'],
                component=alert['component'],
                metrics=alert.get('details', {}),
                actions=self.get_recommended_actions(alert),
                dashboard_url=self.dashboard_url,
                alert_id=alert['id']
            )

            # Create email message
            msg = MIMEMultipart()
            msg['Subject'] = f"[{alert['severity'].upper()}] Terminusa Alert: {alert['title']}"
            msg['From'] = os.getenv('EMAIL_FROM', 'monitoring@terminusa.online')
            msg['To'] = ', '.join(ALERT_CONFIG['channels']['email']['recipients'])
            msg.attach(MIMEText(content, 'html'))

            # Send email
            with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT'))) as server:
                server.starttls()
                server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
                server.send_message(msg)
                
            logger.info(f"Email alert sent: {alert['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def send_slack_alert(self, alert: Dict):
        """Send alert via Slack"""
        try:
            template = self.slack_templates.get(alert['severity'])
            if not template:
                logger.error(f"Slack template not found for severity: {alert['severity']}")
                return

            # Prepare message payload
            payload = {
                'blocks': template['blocks'],
                'color': template['color']
            }

            # Replace template variables
            payload_str = json.dumps(payload)
            for key, value in {
                '{{title}}': alert['title'],
                '{{message}}': alert['message'],
                '{{timestamp}}': alert['timestamp'],
                '{{component}}': alert['component'],
                '{{details}}': json.dumps(alert.get('details', {}), indent=2),
                '{{actions}}': self.get_recommended_actions(alert),
                '{{dashboard_url}}': self.dashboard_url,
                '{{alert_id}}': alert['id']
            }.items():
                payload_str = payload_str.replace(key, str(value))

            # Send to Slack
            webhook_url = ALERT_CONFIG['channels']['slack']['webhook_url']
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=json.loads(payload_str)) as response:
                    if response.status != 200:
                        logger.error(f"Slack API error: {await response.text()}")
                    else:
                        logger.info(f"Slack alert sent: {alert['id']}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def send_websocket_alert(self, alert: Dict):
        """Send alert via WebSocket"""
        try:
            from game_systems.monitoring_websocket import monitoring_websocket
            
            if monitoring_websocket:
                await monitoring_websocket.broadcast({
                    'type': 'alert',
                    'data': {
                        'id': alert['id'],
                        'title': alert['title'],
                        'message': alert['message'],
                        'severity': alert['severity'],
                        'component': alert['component'],
                        'timestamp': alert['timestamp'],
                        'details': alert.get('details', {})
                    }
                })
                
                logger.info(f"WebSocket alert sent: {alert['id']}")
                
        except Exception as e:
            logger.error(f"Failed to send WebSocket alert: {e}")

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

    def get_recommended_actions(self, alert: Dict) -> str:
        """Get recommended actions based on alert type"""
        actions = {
            'system': {
                'critical': [
                    "1. Check system resource usage immediately",
                    "2. Identify and stop resource-intensive processes",
                    "3. Consider scaling up resources if needed"
                ],
                'warning': [
                    "1. Monitor system resource trends",
                    "2. Plan for potential resource upgrades",
                    "3. Review system optimization options"
                ]
            },
            'database': {
                'critical': [
                    "1. Check active database connections",
                    "2. Review and optimize slow queries",
                    "3. Consider connection pooling adjustments"
                ],
                'warning': [
                    "1. Monitor query performance",
                    "2. Review database indexes",
                    "3. Check cache hit ratios"
                ]
            },
            'game': {
                'critical': [
                    "1. Check game server status",
                    "2. Review active player sessions",
                    "3. Monitor transaction processing"
                ],
                'warning': [
                    "1. Monitor player activity trends",
                    "2. Review game performance metrics",
                    "3. Check resource allocation"
                ]
            }
        }

        component_actions = actions.get(alert['component'], {})
        severity_actions = component_actions.get(alert['severity'], ["Monitor the situation"])
        
        return "\n".join(severity_actions)

    def format_details(self, details: Dict) -> str:
        """Format alert details for display"""
        if not details:
            return "No additional details"
            
        formatted = []
        for key, value in details.items():
            if isinstance(value, (int, float)):
                formatted.append(f"{key}: {value:,.2f}")
            else:
                formatted.append(f"{key}: {value}")
                
        return "\n".join(formatted)

# Initialize notification handler
notification_handler = NotificationHandler()
