"""
MongoDB database connection and management.

This module provides a singleton database connection manager for MongoDB
using PyMongo with connection pooling and health checks.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager."""

    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def initialize(self, uri, db_name, max_pool_size=100, min_pool_size=10, 
                   server_selection_timeout_ms=5000, connect_timeout_ms=10000,
                   socket_timeout_ms=20000):
        """
        Initialize MongoDB connection with optimized settings for async operations.

        Args:
            uri (str): MongoDB connection URI.
            db_name (str): Database name.
            max_pool_size (int): Maximum number of connections in the pool.
            min_pool_size (int): Minimum number of connections in the pool.
            server_selection_timeout_ms (int): Server selection timeout in milliseconds.
            connect_timeout_ms (int): Connection timeout in milliseconds.
            socket_timeout_ms (int): Socket timeout in milliseconds.

        Raises:
            ConnectionFailure: If unable to connect to MongoDB.
        """
        try:
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=server_selection_timeout_ms,
                connectTimeoutMS=connect_timeout_ms,
                socketTimeoutMS=socket_timeout_ms,
                maxPoolSize=max_pool_size,
                minPoolSize=min_pool_size,
                retryWrites=True,
                retryReads=True,
                # Optimize for async-like behavior with connection pooling
                maxIdleTimeMS=30000,  # Close idle connections after 30s
                waitQueueTimeoutMS=10000,  # Wait max 10s for a connection from pool
                # Read preference for better load distribution
                readPreference='primaryPreferred',
                # Write concern for better performance (adjust based on requirements)
                w='majority',
                journal=True
            )
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[db_name]
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            logger.info(f"Connection pool: min={min_pool_size}, max={max_pool_size}")
            self._create_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """
        Create database indexes for optimal query performance.
        
        NOTE: This method is DEPRECATED and maintained only for backward compatibility.
        Index creation is now managed through the migration system in migrations/versions/.
        
        For new index definitions, create a migration using:
        1. Create a new migration file in migrations/versions/
        2. Use MigrationManager to apply migrations
        
        See migrations/versions/001_initial_setup.py for index definitions.
        
        This method creates a minimal set of indexes required for application startup.
        Run database migrations for comprehensive index coverage.
        """
        try:
            logger.info("Creating minimal startup indexes (full indexes managed by migrations)")
            
            # Critical unique constraints only (prevents data corruption)
            self._db.users.create_index([('username', ASCENDING)], unique=True, background=True)
            self._db.users.create_index([('email', ASCENDING)], unique=True, background=True)
            self._db.products.create_index([('sku', ASCENDING)], unique=True, background=True)
            self._db.warehouses.create_index([('code', ASCENDING)], unique=True, background=True)
            
            logger.info("Minimal indexes created. Run migrations for comprehensive indexing.")
            logger.warning("DEPRECATED: Use migration system for index management")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def get_db(self):
        """
        Get database instance.

        Returns:
            Database: MongoDB database instance.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db

    def close(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")


# Global database instance
db = Database()


def get_db():
    """
    Get database instance (convenience function).

    Returns:
        Database: MongoDB database instance.
    """
    return db.get_db()
