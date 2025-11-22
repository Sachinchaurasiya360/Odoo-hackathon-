"""
Serialization utilities for consistent data conversion.

This module provides utilities for consistent serialization of MongoDB
data types, particularly ObjectId and datetime objects.
"""

from datetime import datetime
from bson import ObjectId
from typing import Any, Optional


def serialize_object_id(obj_id: Optional[ObjectId]) -> Optional[str]:
    """
    Consistently serialize ObjectId to string.

    Args:
        obj_id: ObjectId instance or None.

    Returns:
        String representation of ObjectId, or None if input is None.
    
    Examples:
        >>> serialize_object_id(ObjectId('507f1f77bcf86cd799439011'))
        '507f1f77bcf86cd799439011'
        >>> serialize_object_id(None)
        None
    """
    if obj_id is None:
        return None
    
    if isinstance(obj_id, ObjectId):
        return str(obj_id)
    
    # If already a string, validate and return
    if isinstance(obj_id, str):
        try:
            ObjectId(obj_id)  # Validate it's a valid ObjectId string
            return obj_id
        except Exception:
            return obj_id  # Return as-is if not valid ObjectId format
    
    return str(obj_id)


def deserialize_object_id(obj_id_str: Optional[str]) -> Optional[ObjectId]:
    """
    Consistently deserialize string to ObjectId.

    Args:
        obj_id_str: String representation of ObjectId or None.

    Returns:
        ObjectId instance, or None if input is None or invalid.
    
    Examples:
        >>> deserialize_object_id('507f1f77bcf86cd799439011')
        ObjectId('507f1f77bcf86cd799439011')
        >>> deserialize_object_id(None)
        None
        >>> deserialize_object_id('invalid')
        None
    """
    if obj_id_str is None:
        return None
    
    if isinstance(obj_id_str, ObjectId):
        return obj_id_str
    
    try:
        return ObjectId(obj_id_str)
    except Exception:
        return None


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Consistently serialize datetime to ISO format string.

    Args:
        dt: datetime instance or None.

    Returns:
        ISO format string, or None if input is None.
    
    Examples:
        >>> serialize_datetime(datetime(2024, 1, 1, 12, 0, 0))
        '2024-01-01T12:00:00'
        >>> serialize_datetime(None)
        None
    """
    if dt is None:
        return None
    
    if isinstance(dt, datetime):
        return dt.isoformat()
    
    return str(dt)


def serialize_document(doc: dict, id_fields: Optional[list] = None) -> dict:
    """
    Serialize a MongoDB document with consistent ObjectId and datetime handling.

    Args:
        doc: MongoDB document dictionary.
        id_fields: List of field names that contain ObjectIds. Defaults to ['_id'].

    Returns:
        Serialized document with string ObjectIds and ISO datetime strings.
    
    Examples:
        >>> doc = {'_id': ObjectId('...'), 'created_at': datetime.utcnow()}
        >>> serialize_document(doc)
        {'_id': '...', 'created_at': '2024-...'}
    """
    if not doc:
        return doc
    
    if id_fields is None:
        id_fields = ['_id']
    
    result = {}
    for key, value in doc.items():
        if key in id_fields or key.endswith('_id'):
            result[key] = serialize_object_id(value)
        elif isinstance(value, datetime):
            result[key] = serialize_datetime(value)
        elif isinstance(value, ObjectId):
            result[key] = serialize_object_id(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_document(item, id_fields) if isinstance(item, dict)
                else serialize_object_id(item) if isinstance(item, ObjectId)
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            result[key] = serialize_document(value, id_fields)
        else:
            result[key] = value
    
    return result


def deserialize_document(doc: dict, id_fields: Optional[list] = None) -> dict:
    """
    Deserialize a document with consistent ObjectId and datetime handling.

    Args:
        doc: Serialized document dictionary.
        id_fields: List of field names that contain ObjectIds. Defaults to ['_id'].

    Returns:
        Document with ObjectId and datetime instances.
    """
    if not doc:
        return doc
    
    if id_fields is None:
        id_fields = ['_id']
    
    result = {}
    for key, value in doc.items():
        if key in id_fields or key.endswith('_id'):
            result[key] = deserialize_object_id(value)
        elif isinstance(value, str):
            # Try to parse as datetime if it looks like ISO format
            try:
                if 'T' in value and len(value) >= 19:
                    result[key] = datetime.fromisoformat(value)
                else:
                    result[key] = value
            except (ValueError, AttributeError):
                result[key] = value
        elif isinstance(value, list):
            result[key] = [
                deserialize_document(item, id_fields) if isinstance(item, dict)
                else deserialize_object_id(item) if isinstance(item, str) and len(item) == 24
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            result[key] = deserialize_document(value, id_fields)
        else:
            result[key] = value
    
    return result
