"""
Adjustment model for stock corrections.

This module defines the Adjustment model for managing stock adjustments
due to physical counts, damage, loss, or found items.
"""

from datetime import datetime
from bson import ObjectId

from utils.constants import (
    ADJUSTMENT_STATUSES, ADJUSTMENT_STATUS_DRAFT, ADJUSTMENT_STATUS_FLOW,
    ADJUSTMENT_TYPES, ADJUSTMENT_TYPE_PHYSICAL_COUNT
)


class Adjustment:
    """Adjustment model for managing stock corrections."""

    def __init__(self, adjustment_number, warehouse_id, product_id,
                 adjustment_type=ADJUSTMENT_TYPE_PHYSICAL_COUNT,
                 status=ADJUSTMENT_STATUS_DRAFT, adjustment_date=None,
                 system_quantity=0, physical_quantity=0, reason='',
                 notes='', created_by=None, approved_by=None, _id=None,
                 created_at=None, updated_at=None):
        """
        Initialize Adjustment instance.

        Args:
            adjustment_number (str): Unique adjustment number.
            warehouse_id (ObjectId): Warehouse ID.
            product_id (ObjectId): Product ID.
            adjustment_type (str): Type of adjustment.
            status (str): Adjustment status.
            adjustment_date (datetime): Date of adjustment.
            system_quantity (float): System-recorded quantity.
            physical_quantity (float): Physically counted quantity.
            reason (str): Reason for adjustment.
            notes (str): Additional notes.
            created_by (ObjectId): User ID who created the adjustment.
            approved_by (ObjectId, optional): User ID who approved the adjustment.
            _id (ObjectId, optional): MongoDB document ID.
            created_at (datetime, optional): Creation timestamp.
            updated_at (datetime, optional): Last update timestamp.
        """
        self._id = _id or ObjectId()
        self.adjustment_number = adjustment_number
        self.warehouse_id = warehouse_id
        self.product_id = product_id
        self.adjustment_type = adjustment_type if adjustment_type in ADJUSTMENT_TYPES else ADJUSTMENT_TYPE_PHYSICAL_COUNT
        self.status = status if status in ADJUSTMENT_STATUSES else ADJUSTMENT_STATUS_DRAFT
        self.adjustment_date = adjustment_date or datetime.utcnow()
        self.system_quantity = system_quantity
        self.physical_quantity = physical_quantity
        self.reason = reason
        self.notes = notes
        self.created_by = created_by
        self.approved_by = approved_by
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def difference(self):
        """
        Calculate difference between physical and system quantity.

        Returns:
            float: Difference (positive means surplus, negative means shortage).
        """
        return self.physical_quantity - self.system_quantity

    def can_transition_to(self, new_status):
        """
        Check if adjustment can transition to new status.

        Args:
            new_status (str): Target status.

        Returns:
            bool: True if transition is allowed.
        """
        allowed_statuses = ADJUSTMENT_STATUS_FLOW.get(self.status, [])
        return new_status in allowed_statuses

    def to_dict(self):
        """
        Convert adjustment to dictionary representation.

        Returns:
            dict: Adjustment data as dictionary.
        """
        return {
            '_id': str(self._id),
            'adjustment_number': self.adjustment_number,
            'warehouse_id': str(self.warehouse_id),
            'product_id': str(self.product_id),
            'adjustment_type': self.adjustment_type,
            'status': self.status,
            'adjustment_date': self.adjustment_date.isoformat() if self.adjustment_date else None,
            'system_quantity': self.system_quantity,
            'physical_quantity': self.physical_quantity,
            'difference': self.difference,
            'reason': self.reason,
            'notes': self.notes,
            'created_by': str(self.created_by) if self.created_by else None,
            'approved_by': str(self.approved_by) if self.approved_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_mongo(self):
        """
        Convert adjustment to MongoDB document format.

        Returns:
            dict: Adjustment data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'adjustment_number': self.adjustment_number,
            'warehouse_id': self.warehouse_id,
            'product_id': self.product_id,
            'adjustment_type': self.adjustment_type,
            'status': self.status,
            'adjustment_date': self.adjustment_date,
            'system_quantity': self.system_quantity,
            'physical_quantity': self.physical_quantity,
            'reason': self.reason,
            'notes': self.notes,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create Adjustment instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            Adjustment: Adjustment instance or None if doc is None.
        """
        if not doc:
            return None
        
        return Adjustment(
            _id=doc.get('_id'),
            adjustment_number=doc.get('adjustment_number'),
            warehouse_id=doc.get('warehouse_id'),
            product_id=doc.get('product_id'),
            adjustment_type=doc.get('adjustment_type', ADJUSTMENT_TYPE_PHYSICAL_COUNT),
            status=doc.get('status', ADJUSTMENT_STATUS_DRAFT),
            adjustment_date=doc.get('adjustment_date'),
            system_quantity=doc.get('system_quantity', 0),
            physical_quantity=doc.get('physical_quantity', 0),
            reason=doc.get('reason', ''),
            notes=doc.get('notes', ''),
            created_by=doc.get('created_by'),
            approved_by=doc.get('approved_by'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )

    def __repr__(self):
        """String representation of Adjustment."""
        return f"<Adjustment {self.adjustment_number} ({self.status}) Diff:{self.difference}>"
