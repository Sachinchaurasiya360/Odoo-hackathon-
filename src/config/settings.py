"""
Configuration settings for the Inventory Management System.

This module provides environment-based configuration classes following
Flask best practices.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    
    DEBUG = False
    TESTING = False

    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable must be set")
    
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'inventory_management')

    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set")
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_ALGORITHM = 'HS256'

    # Pagination settings
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))

    # Cache settings
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))

    # Business logic settings
    ALLOW_NEGATIVE_STOCK = os.getenv('ALLOW_NEGATIVE_STOCK', 'false').lower() == 'true'

    # Email settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@inventory.com')

    # OTP settings
    OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 10))
    OTP_LENGTH = 6

    # Session settings (Redis-backed for horizontal scaling)
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'redis')  # 'redis' for production, 'filesystem' for dev
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'inventory:session:'
    
    # Redis settings for sessions and caching
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    SESSION_REDIS = None  # Will be set in app factory
    
    # Session cookie settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'inventory_session'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # MongoDB async settings
    MONGODB_MAX_POOL_SIZE = int(os.getenv('MONGODB_MAX_POOL_SIZE', 100))
    MONGODB_MIN_POOL_SIZE = int(os.getenv('MONGODB_MIN_POOL_SIZE', 10))
    MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv('MONGODB_TIMEOUT_MS', 5000))
    MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv('MONGODB_CONNECT_TIMEOUT_MS', 10000))
    MONGODB_SOCKET_TIMEOUT_MS = int(os.getenv('MONGODB_SOCKET_TIMEOUT_MS', 20000))
    
    # Application performance settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_TYPE = 'filesystem'  # Use filesystem for local dev (no Redis required)
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.flask_session')


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    MONGODB_DB_NAME = 'inventory_management_test'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    Get configuration object based on environment.

    Args:
        env (str, optional): Environment name. Defaults to FLASK_ENV or 'development'.

    Returns:
        Config: Configuration object for the specified environment.
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
