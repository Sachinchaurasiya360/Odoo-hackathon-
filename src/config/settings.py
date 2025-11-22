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
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://sachinchaurasiya69:606280Sk@tesing.8vhz1.mongodb.net/odoo')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'inventory_management')

    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
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

    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False


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
