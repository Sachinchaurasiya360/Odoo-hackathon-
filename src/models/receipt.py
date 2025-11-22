"""
Receipt model for incoming inventory.

This module defines Receipt and ReceiptItem models for managing
incoming inventory receipts with workflow states.
"""

from datetime import datetime
from bson import ObjectId

from utils.constants import (
    RECEIPT_STATUSES, RECEIPT_STATUS_DRAFT, RECEIPT_STATUS_FLOW
)
from utils.serializers import serialize_object_id, serialize_datetime


class ReceiptItem:
    """ReceiptItem model for individual items in a receipt."""

    def __init__(self, product_id, expected_quantity, received_quantity=0,
                 damaged_quantity=0, unit_price=0, notes=''):
        """
        Initialize ReceiptItem instance.

        Args:
            product_id (ObjectId): Product ID.
            expected_quantity (float): Expected quantity to receive.
            received_quantity (float): Actual quantity received.
            damaged_quantity (float): Quantity damaged.
            unit_price (float): Unit price.
            notes (str): Item-specific notes.
        """
        self.product_id = product_id
        self.expected_quantity = expected_quantity
        self.received_quantity = received_quantity
        self.damaged_quantity = damaged_quantity
        self.unit_price = unit_price
        self.notes = notes

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'product_id': serialize_object_id(self.product_id),
            'expected_quantity': self.expected_quantity,
            'received_quantity': self.received_quantity,
            'damaged_quantity': self.damaged_quantity,
            'unit_price': self.unit_price,
            'notes': self.notes
        }

    def to_mongo(self):
        """Convert to MongoDB format."""
        return {
            'product_id': self.product_id,
            'expected_quantity': self.expected_quantity,
            'received_quantity': self.received_quantity,
            'damaged_quantity': self.damaged_quantity,
            'unit_price': self.unit_price,
            'notes': self.notes
        }

    @staticmethod
    def from_dict(data):
        """Create ReceiptItem from dictionary."""
        return ReceiptItem(
            product_id=ObjectId(data['product_id']) if isinstance(data['product_id'], str) else data['product_id'],
            expected_quantity=data.get('expected_quantity', 0),
            received_quantity=data.get('received_quantity', 0),
            damaged_quantity=data.get('damaged_quantity', 0),
            unit_price=data.get('unit_price', 0),
            notes=data.get('notes', '')
        )


class Receipt:
    """Receipt model for managing incoming inventory."""

    def __init__(self, receipt_number, warehouse_id, supplier_name,
                 status=RECEIPT_STATUS_DRAFT, scheduled_date=None,
                 received_date=None, items=None, notes='', created_by=None,
                 _id=None, created_at=None, updated_at=None, status_history=None):
        """
        Initialize Receipt instance.

        Args:
            receipt_number (str): Unique receipt number.
            warehouse_id (ObjectId): Warehouse ID.
            supplier_name (str): Supplier name.
            status (str): Receipt status.
            scheduled_date (datetime): Scheduled receipt date.
            received_date (datetime, optional): Actual receipt date.
            items (list): List of ReceiptItem instances.
            notes (str): Receipt notes.
            created_by (ObjectId): User ID who created the receipt.
            _id (ObjectId, optional): MongoDB document ID.
            created_at (datetime, optional): Creation timestamp.
            updated_at (datetime, optional): Last update timestamp.
            status_history (list, optional): Status change history.
        """
        self._id = _id or ObjectId()
        self.receipt_number = receipt_number
        self.warehouse_id = warehouse_id
        self.supplier_name = supplier_name
        self.status = status if status in RECEIPT_STATUSES else RECEIPT_STATUS_DRAFT
        self.scheduled_date = scheduled_date or datetime.utcnow()
        self.received_date = received_date
        self.items = items or []
        self.notes = notes
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status_history = status_history or []

    def can_transition_to(self, new_status):
        """
        Check if receipt can transition to new status.

        Args:
            new_status (str): Target status.

        Returns:
            bool: True if transition is allowed.
        """
        allowed_statuses = RECEIPT_STATUS_FLOW.get(self.status, [])
        return new_status in allowed_statuses

    def add_status_history(self, new_status, changed_by):
        """
        Add status change to history.

        Args:
            new_status (str): New status.
            changed_by (ObjectId): User ID who changed the status.
        """
        self.status_history.append({
            'status': new_status,
            'changed_at': datetime.utcnow(),
            'changed_by': changed_by
        })

    def to_dict(self):
        """Convert receipt to dictionary."""
        return {
            '_id': serialize_object_id(self._id),
            'receipt_number': self.receipt_number,
            'warehouse_id': serialize_object_id(self.warehouse_id),
            'supplier_name': self.supplier_name,
            'status': self.status,
            'scheduled_date': serialize_datetime(self.scheduled_date),
            'received_date': serialize_datetime(self.received_date),
            'items': [item.to_dict() for item in self.items],
            'notes': self.notes,
            'created_by': serialize_object_id(self.created_by),
            'created_at': serialize_datetime(self.created_at),
            'updated_at': serialize_datetime(self.updated_at),
            'status_history': [
                {
                    'status': h['status'],
                    'changed_at': serialize_datetime(h['changed_at']),
                    'changed_by': serialize_object_id(h['changed_by'])
                }
                for h in self.status_history
            ]
        }

    def to_mongo(self):
        """Convert receipt to MongoDB format."""
        return {
            '_id': self._id,
            'receipt_number': self.receipt_number,
            'warehouse_id': self.warehouse_id,
            'supplier_name': self.supplier_name,
            'status': self.status,
            'scheduled_date': self.scheduled_date,
            'received_date': self.received_date,
            'items': [item.to_mongo() for item in self.items],
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status_history': self.status_history
        }

    @staticmethod
    def from_mongo(doc):
        """Create Receipt from MongoDB document."""
        if not doc:
            return None
        
        items = [ReceiptItem.from_dict(item) for item in doc.get('items', [])]
        
        return Receipt(
            _id=doc.get('_id'),
            receipt_number=doc.get('receipt_number'),
            warehouse_id=doc.get('warehouse_id'),
            supplier_name=doc.get('supplier_name'),
            status=doc.get('status', RECEIPT_STATUS_DRAFT),
            scheduled_date=doc.get('scheduled_date'),
            received_date=doc.get('received_date'),
            items=items,
            notes=doc.get('notes', ''),
            created_by=doc.get('created_by'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            status_history=doc.get('status_history', [])
        )

    def __repr__(self):
        """String representation of Receipt."""
        return f"<Receipt {self.receipt_number} ({self.status})>"
