"""
Stock models for inventory tracking.

This module defines StockLevel and StockLedger models for managing
real-time stock levels and transaction history.
"""

from datetime import datetime
from bson import ObjectId

from utils.constants import TRANSACTION_TYPES
from utils.serializers import serialize_object_id, serialize_datetime


class StockLevel:
    """StockLevel model for tracking current stock quantities."""

    def __init__(self, product_id, warehouse_id, quantity=0, reserved_quantity=0,
                 _id=None, last_updated=None):
        """
        Initialize StockLevel instance.

        Args:
            product_id (ObjectId): Product ID.
            warehouse_id (ObjectId): Warehouse ID.
            quantity (float): Total quantity in stock.
            reserved_quantity (float): Quantity reserved for pending orders.
            _id (ObjectId, optional): MongoDB document ID.
            last_updated (datetime, optional): Last update timestamp.
        """
        self._id = _id or ObjectId()
        self.product_id = product_id
        self.warehouse_id = warehouse_id
        self.quantity = quantity
        self.reserved_quantity = reserved_quantity
        self.last_updated = last_updated or datetime.utcnow()

    @property
    def available_quantity(self):
        """
        Calculate available quantity (total - reserved).

        Returns:
            float: Available quantity.
        """
        return self.quantity - self.reserved_quantity

    def to_dict(self):
        """
        Convert stock level to dictionary representation.

        Returns:
            dict: Stock level data as dictionary.
        """
        return {
            '_id': serialize_object_id(self._id),
            'product_id': serialize_object_id(self.product_id),
            'warehouse_id': serialize_object_id(self.warehouse_id),
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'last_updated': serialize_datetime(self.last_updated)
        }

    def to_mongo(self):
        """
        Convert stock level to MongoDB document format.

        Returns:
            dict: Stock level data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'product_id': self.product_id,
            'warehouse_id': self.warehouse_id,
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'last_updated': self.last_updated
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create StockLevel instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            StockLevel: StockLevel instance or None if doc is None.
        """
        if not doc:
            return None
        
        return StockLevel(
            _id=doc.get('_id'),
            product_id=doc.get('product_id'),
            warehouse_id=doc.get('warehouse_id'),
            quantity=doc.get('quantity', 0),
            reserved_quantity=doc.get('reserved_quantity', 0),
            last_updated=doc.get('last_updated')
        )

    def __repr__(self):
        """String representation of StockLevel."""
        return f"<StockLevel Product:{self.product_id} Warehouse:{self.warehouse_id} Qty:{self.quantity}>"


class StockLedger:
    """StockLedger model for tracking all stock movements."""

    def __init__(self, product_id, warehouse_id, transaction_type, reference_type,
                 reference_id, reference_number, quantity_change, quantity_before,
                 quantity_after, created_by, notes='', _id=None,
                 transaction_date=None, created_at=None):
        """
        Initialize StockLedger instance.

        Args:
            product_id (ObjectId): Product ID.
            warehouse_id (ObjectId): Warehouse ID.
            transaction_type (str): Type of transaction (must be in TRANSACTION_TYPES).
            reference_type (str): Type of reference document (e.g., 'Receipt', 'Delivery').
            reference_id (ObjectId): Reference document ID.
            reference_number (str): Reference document number.
            quantity_change (float): Quantity change (positive or negative).
            quantity_before (float): Quantity before transaction.
            quantity_after (float): Quantity after transaction.
            created_by (ObjectId): User ID who created the transaction.
            notes (str): Additional notes.
            _id (ObjectId, optional): MongoDB document ID.
            transaction_date (datetime, optional): Transaction timestamp.
            created_at (datetime, optional): Creation timestamp.
        """
        self._id = _id or ObjectId()
        self.product_id = product_id
        self.warehouse_id = warehouse_id
        self.transaction_type = transaction_type
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.reference_number = reference_number
        self.quantity_change = quantity_change
        self.quantity_before = quantity_before
        self.quantity_after = quantity_after
        self.notes = notes
        self.created_by = created_by
        self.transaction_date = transaction_date or datetime.utcnow()
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        """
        Convert stock ledger entry to dictionary representation.

        Returns:
            dict: Stock ledger data as dictionary.
        """
        return {
            '_id': serialize_object_id(self._id),
            'product_id': serialize_object_id(self.product_id),
            'warehouse_id': serialize_object_id(self.warehouse_id),
            'transaction_date': serialize_datetime(self.transaction_date),
            'transaction_type': self.transaction_type,
            'reference_type': self.reference_type,
            'reference_id': serialize_object_id(self.reference_id),
            'reference_number': self.reference_number,
            'quantity_change': self.quantity_change,
            'quantity_before': self.quantity_before,
            'quantity_after': self.quantity_after,
            'notes': self.notes,
            'created_by': serialize_object_id(self.created_by),
            'created_at': serialize_datetime(self.created_at)
        }

    def to_mongo(self):
        """
        Convert stock ledger entry to MongoDB document format.

        Returns:
            dict: Stock ledger data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'product_id': self.product_id,
            'warehouse_id': self.warehouse_id,
            'transaction_date': self.transaction_date,
            'transaction_type': self.transaction_type,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'reference_number': self.reference_number,
            'quantity_change': self.quantity_change,
            'quantity_before': self.quantity_before,
            'quantity_after': self.quantity_after,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create StockLedger instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            StockLedger: StockLedger instance or None if doc is None.
        """
        if not doc:
            return None
        
        return StockLedger(
            _id=doc.get('_id'),
            product_id=doc.get('product_id'),
            warehouse_id=doc.get('warehouse_id'),
            transaction_type=doc.get('transaction_type'),
            reference_type=doc.get('reference_type'),
            reference_id=doc.get('reference_id'),
            reference_number=doc.get('reference_number'),
            quantity_change=doc.get('quantity_change'),
            quantity_before=doc.get('quantity_before'),
            quantity_after=doc.get('quantity_after'),
            created_by=doc.get('created_by'),
            notes=doc.get('notes', ''),
            transaction_date=doc.get('transaction_date'),
            created_at=doc.get('created_at')
        )

    def __repr__(self):
        """String representation of StockLedger."""
        return f"<StockLedger {self.transaction_type} {self.reference_number} Qty:{self.quantity_change}>"
