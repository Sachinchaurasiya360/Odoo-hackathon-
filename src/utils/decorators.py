"""
Custom decorators for authentication and authorization.

This module provides decorators for protecting routes with authentication
and role-based access control.
"""

from functools import wraps
from flask import request, session, redirect, url_for, flash
import jwt
from datetime import datetime
from bson import ObjectId

from config.settings import get_config
from utils.responses import unauthorized_response, forbidden_response
from utils.constants import VALID_ROLES


def login_required(f):
    """
    Decorator to require authentication for a route.

    This decorator checks for a valid JWT token in the Authorization header
    or a valid session.

    Args:
        f: Function to decorate.

    Returns:
        Decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                config = get_config()
                payload = jwt.decode(
                    token,
                    config.JWT_SECRET_KEY,
                    algorithms=[config.JWT_ALGORITHM]
                )
                # Add user info to request context
                request.user_id = payload.get('user_id')
                request.user_role = payload.get('role')
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return unauthorized_response("Token has expired")
            except jwt.InvalidTokenError:
                return unauthorized_response("Invalid token")
        
        # Check for session-based authentication
        elif 'user_id' in session:
            request.user_id = session.get('user_id')
            request.user_role = session.get('user_role')
            return f(*args, **kwargs)
        
        # No valid authentication found
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return unauthorized_response("Authentication required")
        else:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
    
    return decorated_function


def role_required(*roles):
    """
    Decorator to require specific roles for a route.

    This decorator must be used after @login_required.

    Args:
        *roles: Variable number of role names required.

    Returns:
        Decorator function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = getattr(request, 'user_role', None)
            
            if not user_role:
                if request.is_json or request.headers.get('Accept') == 'application/json':
                    return unauthorized_response("Authentication required")
                else:
                    flash('Please log in to access this page.', 'warning')
                    return redirect(url_for('auth.login'))
            
            if user_role not in roles:
                if request.is_json or request.headers.get('Accept') == 'application/json':
                    return forbidden_response("Insufficient permissions")
                else:
                    flash('You do not have permission to access this page.', 'danger')
                    return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to require admin role.

    This is a convenience decorator equivalent to @role_required('admin').

    Args:
        f: Function to decorate.

    Returns:
        Decorated function.
    """
    return role_required('admin')(f)


def api_key_required(f):
    """
    Decorator to require API key authentication.

    This decorator checks for a valid API key in the X-API-Key header.
    Useful for external integrations.

    Args:
        f: Function to decorate.

    Returns:
        Decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return unauthorized_response("API key required")
        
        # TODO: Implement API key validation against database
        # For now, this is a placeholder
        
        return f(*args, **kwargs)
    
    return decorated_function
