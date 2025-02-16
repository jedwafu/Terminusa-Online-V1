import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets
from models import User
from db_setup import db
import logging
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email Configuration
        self.smtp_host = 'localhost'  # Local Postfix server
        self.smtp_port = 25  # Standard SMTP port
        self.from_email = f"noreply@{socket.getfqdn()}"  # Use server's FQDN
        self.verification_url = os.getenv('VERIFICATION_URL', 'https://play.terminusa.online/verify')
        
        # Ensure mail directory exists
        os.makedirs('logs', exist_ok=True)

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using local Postfix SMTP server"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Connect to local SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def send_verification_email(self, user: User) -> bool:
        """Send verification email to user"""
        try:
            # Generate verification token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=24)

            # Update user's verification status
            user.email_verification_token = token
            user.email_verification_sent_at = datetime.utcnow()
            
            db.session.commit()

            # Prepare email
            verification_link = f"{self.verification_url}?token={token}"
            
            html_content = f"""
            <h2>Welcome to Terminusa Online!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Verify Email Address</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not create this account, please ignore this email.</p>
            <br>
            <p>Best regards,</p>
            <p>The Terminusa Online Team</p>
            """

            return self.send_email(
                user.email,
                "Verify your Terminusa Online account",
                html_content
            )

        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            db.session.rollback()
            return False

    def verify_email(self, token: str) -> bool:
        """Verify user's email using token"""
        try:
            user = User.query.filter_by(email_verification_token=token).first()
            if not user:
                logger.warning(f"Invalid verification token: {token}")
                return False

            if user.email_verification_sent_at + timedelta(hours=24) < datetime.utcnow():
                logger.warning(f"Expired verification token: {token}")
                return False

            # Update user's verification status
            user.is_email_verified = True
            user.email_verification_token = None
            
            db.session.commit()
            logger.info(f"Email verified for user {user.email}")

            # Send welcome email
            welcome_html = f"""
            <h2>Welcome to Terminusa Online!</h2>
            <p>Your email has been successfully verified. You now have full access to all features of Terminusa Online.</p>
            <p>Get started by:</p>
            <ul>
                <li>Customizing your profile</li>
                <li>Joining a guild</li>
                <li>Exploring the game world</li>
            </ul>
            <p>If you have any questions, our support team is here to help!</p>
            <br>
            <p>Best regards,</p>
            <p>The Terminusa Online Team</p>
            """
            
            self.send_email(
                user.email,
                "Welcome to Terminusa Online!",
                welcome_html
            )
            
            return True

        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            db.session.rollback()
            return False

    def send_password_reset_email(self, user: User) -> bool:
        """Send password reset email to user"""
        try:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            reset_link = f"{self.verification_url}/reset-password?token={token}"
            
            html_content = f"""
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password. Click the button below to set a new password:</p>
            <p><a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <br>
            <p>Best regards,</p>
            <p>The Terminusa Online Team</p>
            """

            return self.send_email(
                user.email,
                "Reset your Terminusa Online password",
                html_content
            )

        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False

def init_email_service(app):
    """Initialize email service"""
    try:
        # Test SMTP connection
        with smtplib.SMTP('localhost', 25, timeout=5) as server:
            server.verify('test@terminusa.online')
            logger.info("SMTP server connection successful")
            return EmailService()
    except Exception as e:
        logger.error(f"Failed to connect to SMTP server: {str(e)}")
        logger.error("Please ensure Postfix is installed and running.")
        logger.error("Run setup_smtp.sh to configure the SMTP server.")
        return None

# Initialize email service
email_service = None  # Will be initialized by init_email_service
