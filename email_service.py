import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime, timedelta
import secrets
from models import EmailVerification, User
from db_setup import db
import logging

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = Email(os.getenv('SENDGRID_FROM_EMAIL'))
        self.verification_url = os.getenv('VERIFICATION_URL', 'https://play.terminusa.online/verify')

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
            to_email = To(user.email)
            subject = "Verify your Terminusa Online account"
            
            html_content = f"""
            <h2>Welcome to Terminusa Online!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}">Verify Email Address</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not create this account, please ignore this email.</p>
            """
            
            content = Content("text/html", html_content)
            mail = Mail(self.from_email, to_email, subject, content)

            # Send email
            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 201, 202]:
                logging.info(f"Verification email sent to {user.email}")
                return True
            else:
                logging.error(f"Failed to send verification email: {response.status_code}")
                return False

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
            
            to_email = To(user.email)
            subject = "Reset your Terminusa Online password"
            
            html_content = f"""
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password. Click the link below to set a new password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            """
            
            content = Content("text/html", html_content)
            mail = Mail(self.from_email, to_email, subject, content)

            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 201, 202]:
                logging.info(f"Password reset email sent to {user.email}")
                return True
            else:
                logging.error(f"Failed to send password reset email: {response.status_code}")
                return False

        except Exception as e:
            logging.error(f"Error sending password reset email: {str(e)}")
            return False

# Initialize email service
email_service = EmailService()
