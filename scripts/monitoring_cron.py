#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/terminusa/monitoring/cron.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('monitoring_cron')

class MonitoringCron:
    def __init__(self):
        self.cron_jobs = {
            'metrics': self.cleanup_metrics,
            'alerts': self.cleanup_alerts,
            'logs': self.rotate_logs,
            'backup': self.backup_data,
            'health': self.check_health,
            'report': self.generate_report
        }

    def run(self, job_name: str):
        """Run specified cron job"""
        try:
            if job_name not in self.cron_jobs:
                raise ValueError(f"Unknown job: {job_name}")

            logger.info(f"Running cron job: {job_name}")
            self.cron_jobs[job_name]()
            logger.info(f"Cron job completed: {job_name}")

        except Exception as e:
            logger.error(f"Cron job failed: {job_name} - {e}")
            sys.exit(1)

    def cleanup_metrics(self):
        """Clean up old metrics data"""
        try:
            from django.core.management import call_command
            
            # Clean up metrics older than 30 days
            call_command('manage_monitoring', 'purge-metrics', '--days=30', '--force')
            
        except Exception as e:
            logger.error(f"Metrics cleanup failed: {e}")
            raise

    def cleanup_alerts(self):
        """Clean up old alerts"""
        try:
            from django.core.management import call_command
            
            # Clean up alerts older than 90 days
            call_command('manage_monitoring', 'purge-alerts', '--days=90', '--force')
            
        except Exception as e:
            logger.error(f"Alerts cleanup failed: {e}")
            raise

    def rotate_logs(self):
        """Rotate monitoring log files"""
        try:
            log_dir = '/var/log/terminusa/monitoring'
            max_size = 10 * 1024 * 1024  # 10MB
            max_backups = 5

            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(log_dir, filename)
                    
                    # Check file size
                    if os.path.getsize(filepath) > max_size:
                        # Rotate backups
                        for i in range(max_backups - 1, 0, -1):
                            old = f"{filepath}.{i}"
                            new = f"{filepath}.{i+1}"
                            if os.path.exists(old):
                                os.rename(old, new)
                        
                        # Backup current log
                        os.rename(filepath, f"{filepath}.1")
                        
                        # Create new log file
                        open(filepath, 'a').close()
                        os.chmod(filepath, 0o644)
                        
            logger.info("Log rotation completed")
            
        except Exception as e:
            logger.error(f"Log rotation failed: {e}")
            raise

    def backup_data(self):
        """Backup monitoring data"""
        try:
            from django.core.management import call_command
            
            # Create full backup
            call_command('backup_monitoring', '--type=full', '--compress')
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def check_health(self):
        """Check monitoring system health"""
        try:
            from django.core.management import call_command
            
            # Run health check
            call_command('manage_monitoring', 'check')
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    def generate_report(self):
        """Generate monitoring report"""
        try:
            from django.core.management import call_command
            from game_systems.monitoring_init import monitoring
            
            # Get monitoring stats
            stats = monitoring.check_monitoring_status()
            
            # Generate report
            report = [
                "=== Monitoring System Report ===",
                f"Generated: {datetime.utcnow().isoformat()}",
                "",
                "System Status:",
                f"  CPU Usage: {stats['system']['cpu']}%",
                f"  Memory Usage: {stats['system']['memory']}%",
                f"  Disk Usage: {stats['system']['disk']}%",
                "",
                "Metrics:",
                f"  Total Metrics: {stats['metrics']['total']}",
                f"  Last Collection: {stats['metrics']['last_collection']}",
                f"  Storage Used: {stats['metrics']['storage_used']}",
                "",
                "Alerts:",
                f"  Active Alerts: {stats['alerts']['active']}",
                f"  Last Alert: {stats['alerts']['last_alert']}",
                "",
                "Services:",
                *[f"  {service}: {status['status']}"
                  for service, status in stats['services'].items()],
                "",
                "=== End Report ==="
            ]

            # Save report
            report_dir = '/var/log/terminusa/monitoring/reports'
            os.makedirs(report_dir, exist_ok=True)
            
            report_path = os.path.join(
                report_dir,
                f"report_{datetime.utcnow().strftime('%Y%m%d')}.txt"
            )
            
            with open(report_path, 'w') as f:
                f.write('\n'.join(report))
                
            logger.info(f"Report generated: {report_path}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise

def setup_cron_jobs():
    """Setup cron jobs in system"""
    try:
        cron_dir = '/etc/cron.d'
        cron_file = os.path.join(cron_dir, 'terminusa-monitoring')
        
        cron_jobs = [
            # Cleanup jobs
            "0 0 * * * www-data /var/www/terminusa/venv/bin/python /var/www/terminusa/scripts/monitoring_cron.py metrics",
            "0 1 * * * www-data /var/www/terminusa/venv/bin/python /var/www/terminusa/scripts/monitoring_cron.py alerts",
            "0 2 * * * www-data /var/www/terminusa/venv/bin/python /var/www/terminusa/scripts/monitoring_cron.py logs",
            
            # Backup jobs
            "0 3 * * * www-data /var/www/terminusa/venv/bin/python /var/www/terminusa/scripts/monitoring_cron.py backup",
            
            # Health check
            "*/5 * * * * www-data /var/www/terminusa/venv/bin/python /var/www/terminusa/scripts/monitoring_cron.py health",
            
            # Daily report
            "0 4 * * * www-data /var/www/terminusa/venv/bin/python /var/www/terminusa/scripts/monitoring_cron.py report"
        ]
        
        with open(cron_file, 'w') as f:
            f.write("# Terminusa monitoring cron jobs\n")
            f.write("SHELL=/bin/bash\n")
            f.write("PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n\n")
            f.write("\n".join(cron_jobs) + "\n")
            
        os.chmod(cron_file, 0o644)
        logger.info(f"Cron jobs installed: {cron_file}")
        
    except Exception as e:
        logger.error(f"Failed to setup cron jobs: {e}")
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitoring Cron Jobs')
    parser.add_argument('job', choices=['metrics', 'alerts', 'logs', 'backup', 'health', 'report'],
                      help='Cron job to run')
    parser.add_argument('--setup', action='store_true',
                      help='Setup cron jobs in system')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_cron_jobs()
    else:
        cron = MonitoringCron()
        cron.run(args.job)
