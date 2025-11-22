"""
Transfer model for inter-warehouse stock movement.

This module defines Transfer and TransferItem models for managing
stock transfers between warehouses.
"""

from datetime import datetime
from bson import ObjectId

from utils.constants import (
    TRANSFER_STATUSES, TRANSFER_STATUS_DRAFT, TRANSFER_STATUS_FLOW
)


class TransferItem:
    """TransferItem model for individual items in a transfer."""

    def __init__(self, product_id, requested_quantity, transferred_quantity=0,
                 received_quantity=0, notes=''):
        """Initialize TransferItem instance."""
        self.product_id = product_id
        self.requested_quantity = requested_quantity
        self.transferred_quantity = transferred_quantity
        self.received_quantity = received_quantity
        self.notes = notes

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'product_id': str(self.product_id),
            'requested_quantity': self.requested_quantity,
            'transferred_quantity': self.transferred_quantity,
            'received_quantity': self.received_quantity,
            'notes': self.notes
        }

    def to_mongo(self):
        """Convert to MongoDB format."""
        return {
            'product_id': self.product_id,
            'requested_quantity': self.requested_quantity,
            'transferred_quantity': self.transferred_quantity,
            'received_quantity': self.received_quantity,
            'notes': self.notes
        }

    @staticmethod
    def from_dict(data):
        """Create TransferItem from dictionary."""
        return TransferItem(
            product_id=ObjectId(data['product_id']) if isinstance(data['product_id'], str) else data['product_id'],
            requested_quantity=data.get('requested_quantity', 0),
            transferred_quantity=data.get('transferred_quantity', 0),
            received_quantity=data.get('received_quantity', 0),
            notes=data.get('notes', '')
        )


class Transfer:
    """Transfer model for managing inter-warehouse stock transfers."""

    def __init__(self, transfer_number, from_warehouse_id, to_warehouse_id,
                 status=TRANSFER_STATUS_DRAFT, scheduled_date=None,
                 completed_date=None, items=None, notes='', created_by=None,
                 _id=None, created_at=None, updated_at=None, status_history=None):
        """Initialize Transfer instance."""
        self._id = _id or ObjectId()
        self.transfer_number = transfer_number
        self.from_warehouse_id = from_warehouse_id
        self.to_warehouse_id = to_warehouse_id
        self.status = status if status in TRANSFER_STATUSES else TRANSFER_STATUS_DRAFT
        self.scheduled_date = scheduled_date or datetime.utcnow()
        self.completed_date = completed_date
        self.items = items or []
        self.notes = notes
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status_history = status_history or []

    def can_transition_to(self, new_status):
        """Check if transfer can transition to new status."""
        allowed_statuses = TRANSFER_STATUS_FLOW.get(self.status, [])
        return new_status in allowed_statuses

    def add_status_history(self, new_status, changed_by):
        """Add status change to history."""
        self.status_history.append({
            'status': new_status,
            'changed_at': datetime.utcnow(),
            'changed_by': changed_by
        })

    def to_dict(self):
        """Convert transfer to dictionary."""
        return {
            '_id': str(self._id),
            'transfer_number': self.transfer_number,
            'from_warehouse_id': str(self.from_warehouse_id),
            'to_warehouse_id': str(self.to_warehouse_id),
            'status': self.status,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'items': [item.to_dict() for item in self.items],
            'notes': self.notes,
            'created_by': str(self.created_by) if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status_history': [
                {
                    'status': h['status'],
                    'changed_at': h['changed_at'].isoformat() if isinstance(h['changed_at'], datetime) else h['changed_at'],
                    'changed_by': str(h['changed_by'])
                }
                for h in self.status_history
            ]
        }

    def to_mongo(self):
        """Convert transfer to MongoDB format."""
        return {
            '_id': self._id,
            'transfer_number': self.transfer_number,
            'from_warehouse_id': self.from_warehouse_id,
            'to_warehouse_id': self.to_warehouse_id,
            'status': self.status,
            'scheduled_date': self.scheduled_date,
            'completed_date': self.completed_date,
            'items': [item.to_mongo() for item in self.items],
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status_history': self.status_history
        }

    @staticmethod
    def from_mongo(doc):
        """Create Transfer from MongoDB document."""
        if not doc:
            return None
        
        items = [TransferItem.from_dict(item) for item in doc.get('items', [])]
        
        return Transfer(
            _id=doc.get('_id'),
            transfer_number=doc.get('transfer_number'),
            from_warehouse_id=doc.get('from_warehouse_id'),
            to_warehouse_id=doc.get('to_warehouse_id'),
            status=doc.get('status', TRANSFER_STATUS_DRAFT),
            scheduled_date=doc.get('scheduled_date'),
            completed_date=doc.get('completed_date'),
            items=items,
            notes=doc.get('notes', ''),
            created_by=doc.get('created_by'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            status_history=doc.get('status_history', [])
        )

    def __repr__(self):
        """String representation of Transfer."""
        return f"<Transfer {self.transfer_number} ({self.status})>"
