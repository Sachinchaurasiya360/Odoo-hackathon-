"""
Warehouse model.

This module defines the Warehouse model for managing warehouse locations.
"""

from datetime import datetime
from bson import ObjectId


class Warehouse:
    """Warehouse model for managing warehouse locations."""

    def __init__(self, code, name, location='', is_active=True, _id=None,
                 created_at=None, updated_at=None):
        """
        Initialize Warehouse instance.

        Args:
            code (str): Unique warehouse code.
            name (str): Warehouse name.
            location (str): Physical location/address.
            is_active (bool): Whether warehouse is active.
            _id (ObjectId, optional): MongoDB document ID.
            created_at (datetime, optional): Creation timestamp.
            updated_at (datetime, optional): Last update timestamp.
        """
        self._id = _id or ObjectId()
        self.code = code
        self.name = name
        self.location = location
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self):
        """
        Convert warehouse to dictionary representation.

        Returns:
            dict: Warehouse data as dictionary.
        """
        return {
            '_id': str(self._id),
            'code': self.code,
            'name': self.name,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_mongo(self):
        """
        Convert warehouse to MongoDB document format.

        Returns:
            dict: Warehouse data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'code': self.code,
            'name': self.name,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create Warehouse instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            Warehouse: Warehouse instance or None if doc is None.
        """
        if not doc:
            return None
        
        return Warehouse(
            _id=doc.get('_id'),
            code=doc.get('code'),
            name=doc.get('name'),
            location=doc.get('location', ''),
            is_active=doc.get('is_active', True),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )

    def __repr__(self):
        """String representation of Warehouse."""
        return f"<Warehouse {self.code}: {self.name}>"
