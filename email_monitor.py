import logging
import subprocess
import psutil
import time
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Optional
import threading
import queue

class EmailMonitor:
    def __init__(self):
        self.logger = logging.getLogger('email_monitor')
        self.setup_logging()
        self.stats_queue = queue.Queue()
        self.should_run = True
        self.stats_file = "email_stats.json"
        self.load_stats()

    def setup_logging(self):
        """Set up logging configuration"""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        handler = logging.FileHandler('logs/email_monitor.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def load_stats(self):
        """Load email statistics from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {
                    'total_sent': 0,
                    'total_failed': 0,
                    'last_24h': {
                        'sent': 0,
                        'failed': 0
                    },
                    'hourly_stats': [],
                    'last_check': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error loading stats: {e}")
            self.stats = {
                'total_sent': 0,
                'total_failed': 0,
                'last_24h': {
                    'sent': 0,
                    'failed': 0
                },
                'hourly_stats': [],
                'last_check': datetime.now().isoformat()
            }

    def save_stats(self):
        """Save email statistics to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving stats: {e}")

    def check_postfix_status(self) -> Dict:
        """Check Postfix service status"""
        try:
            result = subprocess.run(['systemctl', 'status', 'postfix'], 
                                  capture_output=True, text=True)
            is_running = 'active (running)' in result.stdout
            
            # Get queue size
            queue_result = subprocess.run(['mailq'], capture_output=True, text=True)
            queue_size = len([line for line in queue_result.stdout.split('\n') 
                            if line.startswith('---')])
            
            return {
                'status': 'running' if is_running else 'stopped',
                'queue_size': queue_size
            }
        except Exception as e:
            self.logger.error(f"Error checking Postfix status: {e}")
            return {'status': 'error', 'queue_size': -1}

    def check_opendkim_status(self) -> Dict:
        """Check OpenDKIM service status"""
        try:
            result = subprocess.run(['systemctl', 'status', 'opendkim'], 
                                  capture_output=True, text=True)
            is_running = 'active (running)' in result.stdout
            return {'status': 'running' if is_running else 'stopped'}
        except Exception as e:
            self.logger.error(f"Error checking OpenDKIM status: {e}")
            return {'status': 'error'}

    def parse_mail_log(self) -> Dict:
        """Parse mail log for statistics"""
        try:
            last_check = datetime.fromisoformat(self.stats['last_check'])
            current_time = datetime.now()
            
            with open('/var/log/mail.log', 'r') as f:
                lines = f.readlines()
            
            sent_count = 0
            failed_count = 0
            
            for line in lines:
                try:
                    log_time = datetime.strptime(line[:15], '%b %d %H:%M:%S')
                    # Add current year since log doesn't include it
                    log_time = log_time.replace(year=current_time.year)
                    
                    if log_time > last_check:
                        if 'status=sent' in line:
                            sent_count += 1
                        elif 'status=bounced' in line or 'status=deferred' in line:
                            failed_count += 1
                except Exception as e:
                    self.logger.error(f"Error parsing log line: {e}")
                    continue
            
            self.stats['total_sent'] += sent_count
            self.stats['total_failed'] += failed_count
            
            # Update hourly stats
            hour_stat = {
                'timestamp': current_time.isoformat(),
                'sent': sent_count,
                'failed': failed_count
            }
            self.stats['hourly_stats'].append(hour_stat)
            
            # Keep only last 24 hours
            cutoff_time = current_time - timedelta(hours=24)
            self.stats['hourly_stats'] = [
                stat for stat in self.stats['hourly_stats']
                if datetime.fromisoformat(stat['timestamp']) > cutoff_time
            ]
            
            # Update last 24h stats
            self.stats['last_24h'] = {
                'sent': sum(stat['sent'] for stat in self.stats['hourly_stats']),
                'failed': sum(stat['failed'] for stat in self.stats['hourly_stats'])
            }
            
            self.stats['last_check'] = current_time.isoformat()
            self.save_stats()
            
            return {
                'new_sent': sent_count,
                'new_failed': failed_count,
                'last_24h': self.stats['last_24h']
            }
        except Exception as e:
            self.logger.error(f"Error parsing mail log: {e}")
            return {'error': str(e)}

    def check_disk_space(self) -> Dict:
        """Check disk space for mail spool"""
        try:
            mail_dir = "/var/spool/postfix"
            usage = psutil.disk_usage(mail_dir)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            }
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return {'error': str(e)}

    def monitor_loop(self):
        """Main monitoring loop"""
        while self.should_run:
            try:
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'postfix': self.check_postfix_status(),
                    'opendkim': self.check_opendkim_status(),
                    'mail_stats': self.parse_mail_log(),
                    'disk_space': self.check_disk_space()
                }
                
                self.stats_queue.put(status)
                self.logger.info(f"Status update: {json.dumps(status, indent=2)}")
                
                # Alert on issues
                if status['postfix']['status'] != 'running':
                    self.logger.error("Postfix is not running!")
                if status['opendkim']['status'] != 'running':
                    self.logger.error("OpenDKIM is not running!")
                if status['disk_space'].get('percent', 0) > 90:
                    self.logger.error("Mail spool disk space critical!")
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def start(self):
        """Start the monitoring service"""
        self.logger.info("Starting email monitoring service")
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop(self):
        """Stop the monitoring service"""
        self.logger.info("Stopping email monitoring service")
        self.should_run = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

    def get_latest_stats(self) -> Dict:
        """Get the latest statistics"""
        try:
            return self.stats_queue.get_nowait()
        except queue.Empty:
            return {
                'message': 'No new stats available',
                'last_check': self.stats['last_check']
            }

# Initialize monitor
email_monitor = EmailMonitor()

if __name__ == '__main__':
    email_monitor.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        email_monitor.stop()
