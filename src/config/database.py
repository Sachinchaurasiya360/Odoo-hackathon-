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

    def initialize(self, uri, db_name):
        """
        Initialize MongoDB connection.

        Args:
            uri (str): MongoDB connection URI.
            db_name (str): Database name.

        Raises:
            ConnectionFailure: If unable to connect to MongoDB.
        """
        try:
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10
            )
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[db_name]
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            self._create_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create database indexes for optimal query performance."""
        try:
            # User indexes
            self._db.users.create_index([('username', ASCENDING)], unique=True)
            self._db.users.create_index([('email', ASCENDING)], unique=True)

            # Product indexes
            self._db.products.create_index([('sku', ASCENDING)], unique=True)
            self._db.products.create_index([('category_id', ASCENDING)])
            self._db.products.create_index([('name', ASCENDING)])

            # Warehouse indexes
            self._db.warehouses.create_index([('code', ASCENDING)], unique=True)

            # StockLevel indexes (compound index for uniqueness)
            self._db.stock_levels.create_index(
                [('product_id', ASCENDING), ('warehouse_id', ASCENDING)],
                unique=True
            )
            self._db.stock_levels.create_index([('product_id', ASCENDING)])
            self._db.stock_levels.create_index([('warehouse_id', ASCENDING)])

            # StockLedger indexes
            self._db.stock_ledger.create_index([('product_id', ASCENDING)])
            self._db.stock_ledger.create_index([('warehouse_id', ASCENDING)])
            self._db.stock_ledger.create_index([('transaction_date', DESCENDING)])
            self._db.stock_ledger.create_index([('reference_id', ASCENDING)])

            # Receipt indexes
            self._db.receipts.create_index([('receipt_number', ASCENDING)], unique=True)
            self._db.receipts.create_index([('warehouse_id', ASCENDING)])
            self._db.receipts.create_index([('status', ASCENDING)])
            self._db.receipts.create_index([('created_at', DESCENDING)])

            # Delivery indexes
            self._db.deliveries.create_index([('delivery_number', ASCENDING)], unique=True)
            self._db.deliveries.create_index([('warehouse_id', ASCENDING)])
            self._db.deliveries.create_index([('status', ASCENDING)])
            self._db.deliveries.create_index([('created_at', DESCENDING)])

            # Transfer indexes
            self._db.transfers.create_index([('transfer_number', ASCENDING)], unique=True)
            self._db.transfers.create_index([('from_warehouse_id', ASCENDING)])
            self._db.transfers.create_index([('to_warehouse_id', ASCENDING)])
            self._db.transfers.create_index([('status', ASCENDING)])
            self._db.transfers.create_index([('created_at', DESCENDING)])

            # Adjustment indexes
            self._db.adjustments.create_index([('adjustment_number', ASCENDING)], unique=True)
            self._db.adjustments.create_index([('warehouse_id', ASCENDING)])
            self._db.adjustments.create_index([('product_id', ASCENDING)])
            self._db.adjustments.create_index([('status', ASCENDING)])
            self._db.adjustments.create_index([('created_at', DESCENDING)])

            logger.info("Database indexes created successfully")
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
