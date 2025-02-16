import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets
from models import EmailVerification, User
from db_setup import db
import logging
import os

class EmailService:
    def __init__(self):
        self.smtp_host = "localhost"  # Local Postfix server
        self.smtp_port = 25  # Default SMTP port
        self.from_email = f"noreply@{os.getenv('DOMAIN_NAME', 'terminusa.online')}"
        self.verification_url = os.getenv('VERIFICATION_URL', 'https://play.terminusa.online/verify')

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using local Postfix server"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Connect to local Postfix server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)
                
            logging.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            return False

    def send_verification_email(self, user: User) -> bool:
        """Send verification email to user"""
        try:
            # Generate verification token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=24)

            # Create verification record
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                token=token,
                expires_at=expires_at
            )
            db.session.add(verification)
            
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
            logging.error(f"Error sending verification email: {str(e)}")
            db.session.rollback()
            return False

    def verify_email(self, token: str) -> bool:
        """Verify user's email using token"""
        try:
            verification = EmailVerification.query.filter_by(
                token=token,
                verified_at=None
            ).first()

            if not verification:
                logging.warning(f"Invalid verification token: {token}")
                return False

            if verification.expires_at < datetime.utcnow():
                logging.warning(f"Expired verification token: {token}")
                return False

            # Update verification record
            verification.verified_at = datetime.utcnow()
            
            # Update user's verification status
            user = User.query.get(verification.user_id)
            if user:
                user.is_email_verified = True
                user.email_verification_token = None
                
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
                
                db.session.commit()
                logging.info(f"Email verified for user {user.email}")
                return True
            
            return False

        except Exception as e:
            logging.error(f"Error verifying email: {str(e)}")
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
            logging.error(f"Error sending password reset email: {str(e)}")
            return False

def init_email_service():
    """Initialize email service"""
    return EmailService()

# Initialize email service
email_service = init_email_service()
