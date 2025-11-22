"""
Delivery model for outgoing inventory.

This module defines Delivery and DeliveryItem models for managing
outgoing inventory deliveries with workflow states.
"""

from datetime import datetime
from bson import ObjectId

from utils.constants import (
    DELIVERY_STATUSES, DELIVERY_STATUS_DRAFT, DELIVERY_STATUS_FLOW
)


class DeliveryItem:
    """DeliveryItem model for individual items in a delivery."""

    def __init__(self, product_id, ordered_quantity, picked_quantity=0,
                 packed_quantity=0, validated_quantity=0, unit_price=0, notes=''):
        """Initialize DeliveryItem instance."""
        self.product_id = product_id
        self.ordered_quantity = ordered_quantity
        self.picked_quantity = picked_quantity
        self.packed_quantity = packed_quantity
        self.validated_quantity = validated_quantity
        self.unit_price = unit_price
        self.notes = notes

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'product_id': str(self.product_id),
            'ordered_quantity': self.ordered_quantity,
            'picked_quantity': self.picked_quantity,
            'packed_quantity': self.packed_quantity,
            'validated_quantity': self.validated_quantity,
            'unit_price': self.unit_price,
            'notes': self.notes
        }

    def to_mongo(self):
        """Convert to MongoDB format."""
        return {
            'product_id': self.product_id,
            'ordered_quantity': self.ordered_quantity,
            'picked_quantity': self.picked_quantity,
            'packed_quantity': self.packed_quantity,
            'validated_quantity': self.validated_quantity,
            'unit_price': self.unit_price,
            'notes': self.notes
        }

    @staticmethod
    def from_dict(data):
        """Create DeliveryItem from dictionary."""
        return DeliveryItem(
            product_id=ObjectId(data['product_id']) if isinstance(data['product_id'], str) else data['product_id'],
            ordered_quantity=data.get('ordered_quantity', 0),
            picked_quantity=data.get('picked_quantity', 0),
            packed_quantity=data.get('packed_quantity', 0),
            validated_quantity=data.get('validated_quantity', 0),
            unit_price=data.get('unit_price', 0),
            notes=data.get('notes', '')
        )


class Delivery:
    """Delivery model for managing outgoing inventory."""

    def __init__(self, delivery_number, warehouse_id, customer_name,
                 customer_address='', status=DELIVERY_STATUS_DRAFT,
                 scheduled_date=None, shipped_date=None, items=None,
                 notes='', created_by=None, _id=None, created_at=None,
                 updated_at=None, status_history=None):
        """Initialize Delivery instance."""
        self._id = _id or ObjectId()
        self.delivery_number = delivery_number
        self.warehouse_id = warehouse_id
        self.customer_name = customer_name
        self.customer_address = customer_address
        self.status = status if status in DELIVERY_STATUSES else DELIVERY_STATUS_DRAFT
        self.scheduled_date = scheduled_date or datetime.utcnow()
        self.shipped_date = shipped_date
        self.items = items or []
        self.notes = notes
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status_history = status_history or []

    def can_transition_to(self, new_status):
        """Check if delivery can transition to new status."""
        allowed_statuses = DELIVERY_STATUS_FLOW.get(self.status, [])
        return new_status in allowed_statuses

    def add_status_history(self, new_status, changed_by):
        """Add status change to history."""
        self.status_history.append({
            'status': new_status,
            'changed_at': datetime.utcnow(),
            'changed_by': changed_by
        })

    def to_dict(self):
        """Convert delivery to dictionary."""
        return {
            '_id': str(self._id),
            'delivery_number': self.delivery_number,
            'warehouse_id': str(self.warehouse_id),
            'customer_name': self.customer_name,
            'customer_address': self.customer_address,
            'status': self.status,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'shipped_date': self.shipped_date.isoformat() if self.shipped_date else None,
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
        """Convert delivery to MongoDB format."""
        return {
            '_id': self._id,
            'delivery_number': self.delivery_number,
            'warehouse_id': self.warehouse_id,
            'customer_name': self.customer_name,
            'customer_address': self.customer_address,
            'status': self.status,
            'scheduled_date': self.scheduled_date,
            'shipped_date': self.shipped_date,
            'items': [item.to_mongo() for item in self.items],
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status_history': self.status_history
        }

    @staticmethod
    def from_mongo(doc):
        """Create Delivery from MongoDB document."""
        if not doc:
            return None
        
        items = [DeliveryItem.from_dict(item) for item in doc.get('items', [])]
        
        return Delivery(
            _id=doc.get('_id'),
            delivery_number=doc.get('delivery_number'),
            warehouse_id=doc.get('warehouse_id'),
            customer_name=doc.get('customer_name'),
            customer_address=doc.get('customer_address', ''),
            status=doc.get('status', DELIVERY_STATUS_DRAFT),
            scheduled_date=doc.get('scheduled_date'),
            shipped_date=doc.get('shipped_date'),
            items=items,
            notes=doc.get('notes', ''),
            created_by=doc.get('created_by'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            status_history=doc.get('status_history', [])
        )

    def __repr__(self):
        """String representation of Delivery."""
        return f"<Delivery {self.delivery_number} ({self.status})>"
