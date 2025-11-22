"""
Standard response formatters for API endpoints.

This module provides consistent JSON response formatting across
all API endpoints.
"""

from flask import jsonify
from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
    """
    Format a successful response.

    Args:
        data: Response data (can be dict, list, or any JSON-serializable type).
        message: Success message.
        status_code: HTTP status code.

    Returns:
        tuple: JSON response and status code.
    """
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code


def error_response(message: str, errors: Optional[Dict] = None, status_code: int = 400) -> tuple:
    """
    Format an error response.

    Args:
        message: Error message.
        errors: Dictionary of field-specific errors.
        status_code: HTTP status code.

    Returns:
        tuple: JSON response and status code.
    """
    response = {
        'success': False,
        'message': message
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), status_code


def validation_error_response(errors: Dict, message: str = "Validation failed") -> tuple:
    """
    Format a validation error response.

    Args:
        errors: Dictionary of validation errors.
        message: General error message.

    Returns:
        tuple: JSON response and status code.
    """
    return error_response(message, errors, 422)


def not_found_response(resource: str = "Resource") -> tuple:
    """
    Format a not found response.

    Args:
        resource: Name of the resource that was not found.

    Returns:
        tuple: JSON response and status code.
    """
    return error_response(f"{resource} not found", status_code=404)


def unauthorized_response(message: str = "Unauthorized access") -> tuple:
    """
    Format an unauthorized response.

    Args:
        message: Unauthorized message.

    Returns:
        tuple: JSON response and status code.
    """
    return error_response(message, status_code=401)


def forbidden_response(message: str = "Access forbidden") -> tuple:
    """
    Format a forbidden response.

    Args:
        message: Forbidden message.

    Returns:
        tuple: JSON response and status code.
    """
    return error_response(message, status_code=403)


def paginated_response(items: list, page: int, per_page: int, total: int, message: str = "Success") -> tuple:
    """
    Format a paginated response.

    Args:
        items: List of items for current page.
        page: Current page number.
        per_page: Items per page.
        total: Total number of items.
        message: Success message.

    Returns:
        tuple: JSON response and status code.
    """
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    data = {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    return success_response(data, message)
