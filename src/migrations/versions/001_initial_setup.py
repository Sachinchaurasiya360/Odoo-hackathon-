"""
Initial migration - create base collections and indexes.

Version: 001
Created: 2024-11-22
"""

from migrations.base_migration import BaseMigration
from pymongo import ASCENDING, DESCENDING


class Migration001InitialSetup(BaseMigration):
    """Create initial database structure with all required indexes."""

    version = "001"
    description = "Initial database setup with collections and indexes"

    def upgrade(self):
        """Create collections and indexes for the inventory system."""
        self.log_info("Creating initial database structure...")

        # Create collections if they don't exist
        collections = [
            'users', 'categories', 'products', 'warehouses',
            'stock_levels', 'stock_ledger', 'receipts', 'deliveries',
            'transfers', 'adjustments'
        ]

        for collection_name in collections:
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                self.log_info(f"Created collection: {collection_name}")

        # User indexes
        self.db.users.create_index([('username', ASCENDING)], unique=True, name='idx_username_unique')
        self.db.users.create_index([('email', ASCENDING)], unique=True, name='idx_email_unique')
        self.db.users.create_index([('role', ASCENDING)], name='idx_role')
        self.db.users.create_index([('is_active', ASCENDING)], name='idx_is_active')

        # Category indexes
        self.db.categories.create_index([('name', ASCENDING)], name='idx_category_name')
        self.db.categories.create_index([('parent_id', ASCENDING)], name='idx_parent_id')

        # Product indexes
        self.db.products.create_index([('sku', ASCENDING)], unique=True, name='idx_sku_unique')
        self.db.products.create_index([('name', ASCENDING)], name='idx_product_name')
        self.db.products.create_index([('category_id', ASCENDING)], name='idx_category_id')
        self.db.products.create_index([('is_active', ASCENDING)], name='idx_product_active')
        self.db.products.create_index(
            [('name', 'text'), ('description', 'text')],
            name='idx_product_fulltext'
        )

        # Warehouse indexes
        self.db.warehouses.create_index([('code', ASCENDING)], unique=True, name='idx_warehouse_code_unique')
        self.db.warehouses.create_index([('name', ASCENDING)], name='idx_warehouse_name')
        self.db.warehouses.create_index([('is_active', ASCENDING)], name='idx_warehouse_active')

        # Stock Level indexes (compound index for uniqueness and queries)
        self.db.stock_levels.create_index(
            [('product_id', ASCENDING), ('warehouse_id', ASCENDING)],
            unique=True,
            name='idx_product_warehouse_unique'
        )
        self.db.stock_levels.create_index([('product_id', ASCENDING)], name='idx_stock_product')
        self.db.stock_levels.create_index([('warehouse_id', ASCENDING)], name='idx_stock_warehouse')
        self.db.stock_levels.create_index([('quantity', ASCENDING)], name='idx_stock_quantity')

        # Stock Ledger indexes (for transaction history and reporting)
        self.db.stock_ledger.create_index([('product_id', ASCENDING)], name='idx_ledger_product')
        self.db.stock_ledger.create_index([('warehouse_id', ASCENDING)], name='idx_ledger_warehouse')
        self.db.stock_ledger.create_index([('transaction_date', DESCENDING)], name='idx_ledger_date')
        self.db.stock_ledger.create_index([('transaction_type', ASCENDING)], name='idx_ledger_type')
        self.db.stock_ledger.create_index([('reference_id', ASCENDING)], name='idx_ledger_reference')
        self.db.stock_ledger.create_index([('created_by', ASCENDING)], name='idx_ledger_created_by')
        # Compound index for common queries
        self.db.stock_ledger.create_index(
            [('product_id', ASCENDING), ('warehouse_id', ASCENDING), ('transaction_date', DESCENDING)],
            name='idx_ledger_product_warehouse_date'
        )

        # Receipt indexes
        self.db.receipts.create_index([('receipt_number', ASCENDING)], unique=True, name='idx_receipt_number_unique')
        self.db.receipts.create_index([('warehouse_id', ASCENDING)], name='idx_receipt_warehouse')
        self.db.receipts.create_index([('status', ASCENDING)], name='idx_receipt_status')
        self.db.receipts.create_index([('created_at', DESCENDING)], name='idx_receipt_created')
        self.db.receipts.create_index([('created_by', ASCENDING)], name='idx_receipt_created_by')
        # Compound index for filtering
        self.db.receipts.create_index(
            [('warehouse_id', ASCENDING), ('status', ASCENDING), ('created_at', DESCENDING)],
            name='idx_receipt_warehouse_status_date'
        )

        # Delivery indexes
        self.db.deliveries.create_index([('delivery_number', ASCENDING)], unique=True, name='idx_delivery_number_unique')
        self.db.deliveries.create_index([('warehouse_id', ASCENDING)], name='idx_delivery_warehouse')
        self.db.deliveries.create_index([('status', ASCENDING)], name='idx_delivery_status')
        self.db.deliveries.create_index([('created_at', DESCENDING)], name='idx_delivery_created')
        self.db.deliveries.create_index([('created_by', ASCENDING)], name='idx_delivery_created_by')
        self.db.deliveries.create_index(
            [('warehouse_id', ASCENDING), ('status', ASCENDING), ('created_at', DESCENDING)],
            name='idx_delivery_warehouse_status_date'
        )

        # Transfer indexes
        self.db.transfers.create_index([('transfer_number', ASCENDING)], unique=True, name='idx_transfer_number_unique')
        self.db.transfers.create_index([('from_warehouse_id', ASCENDING)], name='idx_transfer_from')
        self.db.transfers.create_index([('to_warehouse_id', ASCENDING)], name='idx_transfer_to')
        self.db.transfers.create_index([('status', ASCENDING)], name='idx_transfer_status')
        self.db.transfers.create_index([('created_at', DESCENDING)], name='idx_transfer_created')
        self.db.transfers.create_index([('created_by', ASCENDING)], name='idx_transfer_created_by')
        # Compound index for warehouse transfers
        self.db.transfers.create_index(
            [('from_warehouse_id', ASCENDING), ('to_warehouse_id', ASCENDING), ('status', ASCENDING)],
            name='idx_transfer_warehouses_status'
        )

        # Adjustment indexes
        self.db.adjustments.create_index([('adjustment_number', ASCENDING)], unique=True, name='idx_adjustment_number_unique')
        self.db.adjustments.create_index([('warehouse_id', ASCENDING)], name='idx_adjustment_warehouse')
        self.db.adjustments.create_index([('product_id', ASCENDING)], name='idx_adjustment_product')
        self.db.adjustments.create_index([('status', ASCENDING)], name='idx_adjustment_status')
        self.db.adjustments.create_index([('created_at', DESCENDING)], name='idx_adjustment_created')
        self.db.adjustments.create_index([('created_by', ASCENDING)], name='idx_adjustment_created_by')

        self.log_info("Successfully created all indexes")

    def downgrade(self):
        """Drop all indexes and collections (use with caution in production)."""
        self.log_warning("Rolling back initial migration - dropping all collections...")

        collections = [
            'users', 'categories', 'products', 'warehouses',
            'stock_levels', 'stock_ledger', 'receipts', 'deliveries',
            'transfers', 'adjustments'
        ]

        for collection_name in collections:
            if collection_name in self.db.list_collection_names():
                self.db.drop_collection(collection_name)
                self.log_info(f"Dropped collection: {collection_name}")

        self.log_info("Rollback completed")
