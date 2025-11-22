"""
User model for authentication and authorization.

This module defines the User model with password hashing and
role-based access control.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

from utils.constants import VALID_ROLES, ROLE_VIEWER
from utils.serializers import serialize_object_id, serialize_datetime


class User:
    """User model for authentication and authorization."""

    def __init__(self, username, email, password=None, password_hash=None,
                 full_name='', role=ROLE_VIEWER, is_active=True, _id=None,
                 created_at=None, updated_at=None):
        """
        Initialize User instance.

        Args:
            username (str): Unique username.
            email (str): Unique email address.
            password (str, optional): Plain text password (will be hashed).
            password_hash (str, optional): Pre-hashed password.
            full_name (str): User's full name.
            role (str): User role (must be in VALID_ROLES).
            is_active (bool): Whether user account is active.
            _id (ObjectId, optional): MongoDB document ID.
            created_at (datetime, optional): Creation timestamp.
            updated_at (datetime, optional): Last update timestamp.
        """
        self._id = _id or ObjectId()
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role if role in VALID_ROLES else ROLE_VIEWER
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        if password:
            self.password_hash = generate_password_hash(password)
        elif password_hash:
            self.password_hash = password_hash
        else:
            raise ValueError("Either password or password_hash must be provided")

    def check_password(self, password):
        """
        Verify password against stored hash.

        Args:
            password (str): Plain text password to verify.

        Returns:
            bool: True if password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        """
        Set new password (hashed).

        Args:
            password (str): Plain text password to set.
        """
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.utcnow()

    def has_role(self, role):
        """
        Check if user has a specific role.

        Args:
            role (str): Role to check.

        Returns:
            bool: True if user has the role, False otherwise.
        """
        return self.role == role

    def has_any_role(self, roles):
        """
        Check if user has any of the specified roles.

        Args:
            roles (list): List of roles to check.

        Returns:
            bool: True if user has any of the roles, False otherwise.
        """
        return self.role in roles

    def to_dict(self, include_sensitive=False):
        """
        Convert user to dictionary representation.

        Args:
            include_sensitive (bool): Whether to include sensitive data.

        Returns:
            dict: User data as dictionary.
        """
        data = {
            '_id': serialize_object_id(self._id),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': serialize_datetime(self.created_at),
            'updated_at': serialize_datetime(self.updated_at)
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data

    def to_mongo(self):
        """
        Convert user to MongoDB document format.

        Returns:
            dict: User data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create User instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            User: User instance or None if doc is None.
        """
        if not doc:
            return None
        
        return User(
            _id=doc.get('_id'),
            username=doc.get('username'),
            email=doc.get('email'),
            password_hash=doc.get('password_hash'),
            full_name=doc.get('full_name', ''),
            role=doc.get('role', ROLE_VIEWER),
            is_active=doc.get('is_active', True),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )

    def __repr__(self):
        """String representation of User."""
        return f"<User {self.username} ({self.role})>"
