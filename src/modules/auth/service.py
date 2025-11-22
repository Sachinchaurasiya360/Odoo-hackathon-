"""
Authentication Service.

This module handles user authentication, registration, and JWT token management.
"""

from datetime import datetime, timedelta
from bson import ObjectId
import jwt
import random
import string

from config.database import get_db
from config.settings import get_config
from models.user import User
from utils.validators import is_valid_email, is_valid_username
from utils.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and user management."""

    def __init__(self):
        """Initialize AuthService."""
        self.db = get_db()
        self.config = get_config()
        self.email_service = EmailService()

    def register_user(self, username, email, password, full_name='', role='viewer'):
        """
        Register a new user.

        Args:
            username (str): Unique username.
            email (str): Unique email address.
            password (str): Plain text password (will be hashed).
            full_name (str): User's full name.
            role (str): User role.

        Returns:
            dict: Result with success status and user data.

        Raises:
            ValueError: If validation fails or user already exists.
        """
        # Validate input
        if not is_valid_username(username):
            raise ValueError("Invalid username format (3-30 alphanumeric characters)")
        
        if not is_valid_email(email):
            raise ValueError("Invalid email format")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        # Check if user already exists
        existing_user = self.db.users.find_one({
            '$or': [
                {'username': username},
                {'email': email}
            ]
        })

        if existing_user:
            if existing_user['username'] == username:
                raise ValueError("Username already exists")
            else:
                raise ValueError("Email already exists")

        # Create new user
        user = User(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role
        )

        # Insert into database
        self.db.users.insert_one(user.to_mongo())

        logger.info(f"New user registered: {username}")

        return {
            'success': True,
            'user': user.to_dict()
        }

    def login(self, username, password):
        """
        Authenticate user and generate JWT token.

        Args:
            username (str): Username or email.
            password (str): Plain text password.

        Returns:
            dict: Result with success status, user data, and JWT token.

        Raises:
            ValueError: If authentication fails.
        """
        # Find user by username or email
        user_doc = self.db.users.find_one({
            '$or': [
                {'username': username},
                {'email': username}
            ]
        })

        if not user_doc:
            raise ValueError("Invalid username or password")

        user = User.from_mongo(user_doc)

        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is disabled")

        # Verify password
        if not user.check_password(password):
            raise ValueError("Invalid username or password")

        # Generate JWT token
        token = self._generate_token(user)

        logger.info(f"User logged in: {username}")

        return {
            'success': True,
            'user': user.to_dict(),
            'token': token
        }

    def _generate_token(self, user):
        """
        Generate JWT token for user.

        Args:
            user (User): User instance.

        Returns:
            str: JWT token.
        """
        payload = {
            'user_id': str(user._id),
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + self.config.JWT_ACCESS_TOKEN_EXPIRES,
            'iat': datetime.utcnow()
        }

        token = jwt.encode(
            payload,
            self.config.JWT_SECRET_KEY,
            algorithm=self.config.JWT_ALGORITHM
        )

        return token

    def verify_token(self, token):
        """
        Verify JWT token and return user data.

        Args:
            token (str): JWT token.

        Returns:
            dict: User data from token.

        Raises:
            jwt.ExpiredSignatureError: If token has expired.
            jwt.InvalidTokenError: If token is invalid.
        """
        payload = jwt.decode(
            token,
            self.config.JWT_SECRET_KEY,
            algorithms=[self.config.JWT_ALGORITHM]
        )

        return payload

    def get_user_by_id(self, user_id):
        """
        Get user by ID.

        Args:
            user_id (str or ObjectId): User ID.

        Returns:
            dict: User data or None.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        user_doc = self.db.users.find_one({'_id': user_id})
        
        if user_doc:
            user = User.from_mongo(user_doc)
            return user.to_dict()
        
        return None

    def update_user(self, user_id, **kwargs):
        """
        Update user information.

        Args:
            user_id (str or ObjectId): User ID.
            **kwargs: Fields to update.

        Returns:
            dict: Result with success status.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Remove sensitive fields that shouldn't be updated directly
        kwargs.pop('password_hash', None)
        kwargs.pop('_id', None)

        kwargs['updated_at'] = datetime.utcnow()

        result = self.db.users.update_one(
            {'_id': user_id},
            {'$set': kwargs}
        )

        if result.modified_count > 0:
            logger.info(f"User updated: {user_id}")
            return {'success': True}
        
        return {'success': False, 'message': 'User not found or no changes made'}

    def change_password(self, user_id, old_password, new_password):
        """
        Change user password.

        Args:
            user_id (str or ObjectId): User ID.
            old_password (str): Current password.
            new_password (str): New password.

        Returns:
            dict: Result with success status.

        Raises:
            ValueError: If old password is incorrect or new password is invalid.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")

        user_doc = self.db.users.find_one({'_id': user_id})
        
        if not user_doc:
            raise ValueError("User not found")

        user = User.from_mongo(user_doc)

        # Verify old password
        if not user.check_password(old_password):
            raise ValueError("Current password is incorrect")

        # Set new password
        user.set_password(new_password)

        # Update in database
        self.db.users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'password_hash': user.password_hash,
                    'updated_at': user.updated_at
                }
            }
        )

        logger.info(f"Password changed for user: {user_id}")

        return {'success': True, 'message': 'Password changed successfully'}

    def generate_otp(self):
        """
        Generate a random OTP code.

        Returns:
            str: OTP code.
        """
        return ''.join(random.choices(string.digits, k=self.config.OTP_LENGTH))

    def request_password_reset(self, email):
        """
        Request password reset by email.

        Generates an OTP and sends it to the user's email.

        Args:
            email (str): User's email address.

        Returns:
            dict: Result with success status.

        Raises:
            ValueError: If email is invalid or user not found.
        """
        if not is_valid_email(email):
            raise ValueError("Invalid email format")

        # Find user by email
        user_doc = self.db.users.find_one({'email': email})

        if not user_doc:
            # For security, don't reveal if email exists
            # But log it
            logger.warning(f"Password reset requested for non-existent email: {email}")
            # Still return success to prevent email enumeration
            return {
                'success': True,
                'message': 'If the email exists, an OTP has been sent'
            }

        user = User.from_mongo(user_doc)

        if not user.is_active:
            raise ValueError("User account is disabled")

        # Generate OTP
        otp_code = self.generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=self.config.OTP_EXPIRY_MINUTES)

        # Store OTP in database
        self.db.users.update_one(
            {'_id': user._id},
            {
                '$set': {
                    'reset_otp': otp_code,
                    'reset_otp_expiry': otp_expiry,
                    'reset_otp_attempts': 0
                }
            }
        )

        # Send OTP email
        email_sent = self.email_service.send_otp_email(
            to_email=email,
            username=user.username,
            otp_code=otp_code
        )

        if email_sent:
            logger.info(f"Password reset OTP sent to {email}")
        else:
            logger.error(f"Failed to send OTP email to {email}")
            # In development, still proceed but log the OTP
            if self.config.DEBUG:
                logger.info(f"[DEV MODE] OTP for {email}: {otp_code}")

        return {
            'success': True,
            'message': 'If the email exists, an OTP has been sent',
            'debug_otp': otp_code if self.config.DEBUG else None  # Only in debug mode
        }

    def verify_otp(self, email, otp_code):
        """
        Verify OTP code for password reset.

        Args:
            email (str): User's email address.
            otp_code (str): OTP code to verify.

        Returns:
            dict: Result with success status and reset token.

        Raises:
            ValueError: If OTP is invalid or expired.
        """
        user_doc = self.db.users.find_one({'email': email})

        if not user_doc:
            raise ValueError("Invalid OTP")

        # Check if OTP exists
        if not user_doc.get('reset_otp'):
            raise ValueError("No OTP request found. Please request a new OTP.")

        # Check OTP expiry
        if user_doc.get('reset_otp_expiry') < datetime.utcnow():
            # Clear expired OTP
            self.db.users.update_one(
                {'_id': user_doc['_id']},
                {
                    '$unset': {
                        'reset_otp': '',
                        'reset_otp_expiry': '',
                        'reset_otp_attempts': ''
                    }
                }
            )
            raise ValueError("OTP has expired. Please request a new one.")

        # Check attempts (prevent brute force)
        attempts = user_doc.get('reset_otp_attempts', 0)
        if attempts >= 5:
            # Clear OTP after too many attempts
            self.db.users.update_one(
                {'_id': user_doc['_id']},
                {
                    '$unset': {
                        'reset_otp': '',
                        'reset_otp_expiry': '',
                        'reset_otp_attempts': ''
                    }
                }
            )
            raise ValueError("Too many failed attempts. Please request a new OTP.")

        # Verify OTP
        if user_doc.get('reset_otp') != otp_code:
            # Increment attempts
            self.db.users.update_one(
                {'_id': user_doc['_id']},
                {'$inc': {'reset_otp_attempts': 1}}
            )
            remaining_attempts = 5 - (attempts + 1)
            raise ValueError(f"Invalid OTP. {remaining_attempts} attempts remaining.")

        # OTP is valid - generate a reset token
        reset_token = self._generate_reset_token(user_doc['_id'])

        # Clear OTP and store reset token
        self.db.users.update_one(
            {'_id': user_doc['_id']},
            {
                '$set': {
                    'reset_token': reset_token,
                    'reset_token_expiry': datetime.utcnow() + timedelta(minutes=15)
                },
                '$unset': {
                    'reset_otp': '',
                    'reset_otp_expiry': '',
                    'reset_otp_attempts': ''
                }
            }
        )

        logger.info(f"OTP verified for user: {email}")

        return {
            'success': True,
            'message': 'OTP verified successfully',
            'reset_token': reset_token
        }

    def reset_password(self, reset_token, new_password):
        """
        Reset password using reset token.

        Args:
            reset_token (str): Reset token from OTP verification.
            new_password (str): New password.

        Returns:
            dict: Result with success status.

        Raises:
            ValueError: If token is invalid or password is weak.
        """
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")

        # Find user with valid reset token
        user_doc = self.db.users.find_one({
            'reset_token': reset_token,
            'reset_token_expiry': {'$gt': datetime.utcnow()}
        })

        if not user_doc:
            raise ValueError("Invalid or expired reset token")

        user = User.from_mongo(user_doc)
        user.set_password(new_password)

        # Update password and clear reset token
        self.db.users.update_one(
            {'_id': user._id},
            {
                '$set': {
                    'password_hash': user.password_hash,
                    'updated_at': user.updated_at
                },
                '$unset': {
                    'reset_token': '',
                    'reset_token_expiry': ''
                }
            }
        )

        logger.info(f"Password reset successfully for user: {user.username}")

        return {
            'success': True,
            'message': 'Password reset successfully'
        }

    def _generate_reset_token(self, user_id):
        """
        Generate a secure reset token.

        Args:
            user_id (ObjectId): User ID.

        Returns:
            str: Reset token.
        """
        payload = {
            'user_id': str(user_id),
            'type': 'password_reset',
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(
            payload,
            self.config.JWT_SECRET_KEY,
            algorithm=self.config.JWT_ALGORITHM
        )

        return token
