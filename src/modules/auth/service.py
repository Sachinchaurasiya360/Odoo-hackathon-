"""
Authentication Service.

This module handles user authentication, registration, and JWT token management.
"""

from datetime import datetime, timedelta
from bson import ObjectId
import jwt

from config.database import get_db
from config.settings import get_config
from models.user import User
from utils.validators import is_valid_email, is_valid_username
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and user management."""

    def __init__(self):
        """Initialize AuthService."""
        self.db = get_db()
        self.config = get_config()

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
