"""
Product and Category models.

This module defines Product and Category models for managing
product catalog and categorization.
"""

from datetime import datetime
from bson import ObjectId

from utils.constants import VALID_UNITS, UNIT_PIECES


class Category:
    """Category model for product categorization."""

    def __init__(self, name, description='', parent_id=None, _id=None,
                 created_at=None):
        """
        Initialize Category instance.

        Args:
            name (str): Category name.
            description (str): Category description.
            parent_id (ObjectId, optional): Parent category ID for hierarchical structure.
            _id (ObjectId, optional): MongoDB document ID.
            created_at (datetime, optional): Creation timestamp.
        """
        self._id = _id or ObjectId()
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        """
        Convert category to dictionary representation.

        Returns:
            dict: Category data as dictionary.
        """
        return {
            '_id': str(self._id),
            'name': self.name,
            'description': self.description,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_mongo(self):
        """
        Convert category to MongoDB document format.

        Returns:
            dict: Category data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'created_at': self.created_at
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create Category instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            Category: Category instance or None if doc is None.
        """
        if not doc:
            return None
        
        return Category(
            _id=doc.get('_id'),
            name=doc.get('name'),
            description=doc.get('description', ''),
            parent_id=doc.get('parent_id'),
            created_at=doc.get('created_at')
        )

    def __repr__(self):
        """String representation of Category."""
        return f"<Category {self.name}>"


class Product:
    """Product model for managing product catalog."""

    def __init__(self, sku, name, description='', category_id=None,
                 unit=UNIT_PIECES, reorder_level=0, is_active=True,
                 _id=None, created_at=None, updated_at=None):
        """
        Initialize Product instance.

        Args:
            sku (str): Unique stock keeping unit code.
            name (str): Product name.
            description (str): Product description.
            category_id (ObjectId, optional): Category ID.
            unit (str): Unit of measurement (must be in VALID_UNITS).
            reorder_level (int): Minimum stock level before reorder alert.
            is_active (bool): Whether product is active.
            _id (ObjectId, optional): MongoDB document ID.
            created_at (datetime, optional): Creation timestamp.
            updated_at (datetime, optional): Last update timestamp.
        """
        self._id = _id or ObjectId()
        self.sku = sku
        self.name = name
        self.description = description
        self.category_id = category_id
        self.unit = unit if unit in VALID_UNITS else UNIT_PIECES
        self.reorder_level = reorder_level
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self):
        """
        Convert product to dictionary representation.

        Returns:
            dict: Product data as dictionary.
        """
        return {
            '_id': str(self._id),
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category_id': str(self.category_id) if self.category_id else None,
            'unit': self.unit,
            'reorder_level': self.reorder_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_mongo(self):
        """
        Convert product to MongoDB document format.

        Returns:
            dict: Product data for MongoDB insertion.
        """
        return {
            '_id': self._id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'unit': self.unit,
            'reorder_level': self.reorder_level,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_mongo(doc):
        """
        Create Product instance from MongoDB document.

        Args:
            doc (dict): MongoDB document.

        Returns:
            Product: Product instance or None if doc is None.
        """
        if not doc:
            return None
        
        return Product(
            _id=doc.get('_id'),
            sku=doc.get('sku'),
            name=doc.get('name'),
            description=doc.get('description', ''),
            category_id=doc.get('category_id'),
            unit=doc.get('unit', UNIT_PIECES),
            reorder_level=doc.get('reorder_level', 0),
            is_active=doc.get('is_active', True),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )

    def __repr__(self):
        """String representation of Product."""
        return f"<Product {self.sku}: {self.name}>"
