"""
Email service for sending emails.

This module handles email sending functionality including OTP emails
for password reset.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import get_config
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        """Initialize EmailService."""
        self.config = get_config()

    def send_email(self, to_email, subject, html_body, text_body=None):
        """
        Send an email.

        Args:
            to_email (str): Recipient email address.
            subject (str): Email subject.
            html_body (str): HTML email body.
            text_body (str, optional): Plain text email body.

        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        if not self.config.MAIL_USERNAME or not self.config.MAIL_PASSWORD:
            logger.warning("Email credentials not configured. Email not sent.")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.MAIL_DEFAULT_SENDER
            msg['To'] = to_email

            # Add text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)

            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

            # Send email
            if self.config.MAIL_USE_SSL:
                server = smtplib.SMTP_SSL(
                    self.config.MAIL_SERVER,
                    self.config.MAIL_PORT
                )
            else:
                server = smtplib.SMTP(
                    self.config.MAIL_SERVER,
                    self.config.MAIL_PORT
                )
                if self.config.MAIL_USE_TLS:
                    server.starttls()

            server.login(self.config.MAIL_USERNAME, self.config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_otp_email(self, to_email, username, otp_code):
        """
        Send OTP email for password reset.

        Args:
            to_email (str): Recipient email address.
            username (str): Username.
            otp_code (str): OTP code.

        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        subject = "Password Reset OTP - Inventory Management System"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #0d6efd;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-code {{
                    background-color: #fff;
                    border: 2px solid #0d6efd;
                    border-radius: 5px;
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px;
                    margin: 20px 0;
                    letter-spacing: 5px;
                    color: #0d6efd;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{username}</strong>,</p>
                    
                    <p>We received a request to reset your password for the Inventory Management System.</p>
                    
                    <p>Your One-Time Password (OTP) is:</p>
                    
                    <div class="otp-code">{otp_code}</div>
                    
                    <p>This OTP will expire in <strong>{self.config.OTP_EXPIRY_MINUTES} minutes</strong>.</p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul>
                            <li>Never share this OTP with anyone</li>
                            <li>Our team will never ask for your OTP</li>
                            <li>If you didn't request this, please ignore this email</li>
                        </ul>
                    </div>
                    
                    <p>Enter this OTP on the password reset page to continue.</p>
                    
                    <p>Best regards,<br>Inventory Management Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply to this email.</p>
                    <p>&copy; 2024 Inventory Management System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Password Reset Request - Inventory Management System
        
        Hello {username},
        
        We received a request to reset your password.
        
        Your One-Time Password (OTP) is: {otp_code}
        
        This OTP will expire in {self.config.OTP_EXPIRY_MINUTES} minutes.
        
        Security Notice:
        - Never share this OTP with anyone
        - Our team will never ask for your OTP
        - If you didn't request this, please ignore this email
        
        Enter this OTP on the password reset page to continue.
        
        Best regards,
        Inventory Management Team
        
        ---
        This is an automated message, please do not reply to this email.
        """

        return self.send_email(to_email, subject, html_body, text_body)
