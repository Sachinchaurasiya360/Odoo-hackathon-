"""
Input validation utilities.

This module provides helper functions for validating and sanitizing
user input to prevent security vulnerabilities.
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate.

    Returns:
        bool: True if valid email format, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    """
    Validate username format (alphanumeric and underscores, 3-30 chars).

    Args:
        username: Username to validate.

    Returns:
        bool: True if valid username, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username))


def is_valid_sku(sku: str) -> bool:
    """
    Validate SKU format (alphanumeric and hyphens, 2-50 chars).

    Args:
        sku: SKU to validate.

    Returns:
        bool: True if valid SKU, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9-]{2,50}$'
    return bool(re.match(pattern, sku))


def is_valid_object_id(id_string: str) -> bool:
    """
    Validate MongoDB ObjectId format.

    Args:
        id_string: String to validate as ObjectId.

    Returns:
        bool: True if valid ObjectId, False otherwise.
    """
    try:
        ObjectId(id_string)
        return True
    except (InvalidId, TypeError):
        return False


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input by removing dangerous characters.

    Args:
        value: String to sanitize.
        max_length: Maximum allowed length.

    Returns:
        str: Sanitized string.
    """
    if not isinstance(value, str):
        return ""
    
    # Remove null bytes and control characters
    sanitized = value.replace('\x00', '').strip()
    
    if max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_required_fields(data: Dict, required_fields: List[str]) -> Dict[str, str]:
    """
    Validate that required fields are present and not empty.

    Args:
        data: Dictionary of data to validate.
        required_fields: List of required field names.

    Returns:
        dict: Dictionary of validation errors (empty if valid).
    """
    errors = {}
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors[field] = f"{field} is required"
    return errors


def validate_positive_number(value: Any, field_name: str = "Value") -> Optional[str]:
    """
    Validate that a value is a positive number.

    Args:
        value: Value to validate.
        field_name: Name of the field for error message.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    try:
        num = float(value)
        if num <= 0:
            return f"{field_name} must be a positive number"
        return None
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number"


def validate_non_negative_number(value: Any, field_name: str = "Value") -> Optional[str]:
    """
    Validate that a value is a non-negative number.

    Args:
        value: Value to validate.
        field_name: Name of the field for error message.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    try:
        num = float(value)
        if num < 0:
            return f"{field_name} cannot be negative"
        return None
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number"


def validate_date(date_string: str, field_name: str = "Date") -> Optional[str]:
    """
    Validate date string format (YYYY-MM-DD).

    Args:
        date_string: Date string to validate.
        field_name: Name of the field for error message.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return None
    except (ValueError, TypeError):
        return f"{field_name} must be in YYYY-MM-DD format"


def validate_choice(value: Any, choices: List[Any], field_name: str = "Value") -> Optional[str]:
    """
    Validate that a value is in a list of valid choices.

    Args:
        value: Value to validate.
        choices: List of valid choices.
        field_name: Name of the field for error message.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    if value not in choices:
        return f"{field_name} must be one of: {', '.join(map(str, choices))}"
    return None


def validate_min_length(value: str, min_length: int, field_name: str = "Value") -> Optional[str]:
    """
    Validate minimum string length.

    Args:
        value: String to validate.
        min_length: Minimum required length.
        field_name: Name of the field for error message.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    if not isinstance(value, str) or len(value) < min_length:
        return f"{field_name} must be at least {min_length} characters"
    return None


def validate_max_length(value: str, max_length: int, field_name: str = "Value") -> Optional[str]:
    """
    Validate maximum string length.

    Args:
        value: String to validate.
        max_length: Maximum allowed length.
        field_name: Name of the field for error message.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    if isinstance(value, str) and len(value) > max_length:
        return f"{field_name} must not exceed {max_length} characters"
    return None
