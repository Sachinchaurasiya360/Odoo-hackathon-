"""
Security middleware and utilities.

This module provides security enhancements including:
- CSRF protection
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Rate limiting
- Request validation
"""

from flask import request, abort, session, current_app
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import logging
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


# Rate limiting storage (use Redis in production)
rate_limit_storage = defaultdict(list)
rate_limit_lock = Lock()


class SecurityHeaders:
    """Security headers middleware for Flask."""
    
    @staticmethod
    def init_app(app):
        """
        Initialize security headers for the application.
        
        Args:
            app: Flask application instance
        """
        @app.after_request
        def set_security_headers(response):
            """Add security headers to all responses."""
            
            # Strict-Transport-Security (HSTS)
            if app.config.get('SESSION_COOKIE_SECURE', False):
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Content-Security-Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # X-Content-Type-Options
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # X-Frame-Options
            response.headers['X-Frame-Options'] = 'DENY'
            
            # X-XSS-Protection (legacy browsers)
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer-Policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # Remove server header
            response.headers.pop('Server', None)
            
            return response
        
        logger.info("Security headers middleware initialized")


class CSRFProtection:
    """CSRF protection middleware."""
    
    EXEMPT_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}
    
    @staticmethod
    def init_app(app):
        """
        Initialize CSRF protection for the application.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def csrf_protect():
            """Validate CSRF token on state-changing requests."""
            
            # Skip CSRF check for exempt methods
            if request.method in CSRFProtection.EXEMPT_METHODS:
                return None
            
            # Skip CSRF check for API endpoints with JWT
            if request.path.startswith('/api/'):
                return None
            
            # Get token from form or header
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            
            # Validate token
            if not token or not CSRFProtection.validate_token(token):
                logger.warning(f"CSRF validation failed for {request.path} from {request.remote_addr}")
                abort(403, description="CSRF token validation failed")
            
            return None
        
        # Add CSRF token to template context
        @app.context_processor
        def inject_csrf_token():
            """Inject CSRF token into all templates."""
            return {
                'csrf_token': CSRFProtection.generate_token,
                'get_csrf_token': CSRFProtection.generate_token
            }
        
        logger.info("CSRF protection initialized")
    
    @staticmethod
    def generate_token():
        """
        Generate a CSRF token for the current session.
        
        Returns:
            str: CSRF token
        """
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        
        return session['csrf_token']
    
    @staticmethod
    def validate_token(token):
        """
        Validate a CSRF token.
        
        Args:
            token: Token to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        session_token = session.get('csrf_token')
        if not session_token:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(token, session_token)


class RateLimiter:
    """Rate limiting middleware."""
    
    @staticmethod
    def init_app(app):
        """
        Initialize rate limiting for the application.
        
        Args:
            app: Flask application instance
        """
        # Store app config
        RateLimiter.app = app
        logger.info("Rate limiter initialized")
    
    @staticmethod
    def limit(max_requests=5, window_seconds=60, key_func=None):
        """
        Rate limiting decorator.
        
        Args:
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
            key_func: Function to generate rate limit key (default: IP address)
            
        Returns:
            Decorator function
            
        Example:
            @RateLimiter.limit(max_requests=5, window_seconds=60)
            def login():
                pass
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Generate rate limit key
                if key_func:
                    key = key_func()
                else:
                    # Default: IP address + endpoint
                    key = f"{request.remote_addr}:{request.endpoint}"
                
                # Check rate limit
                if not RateLimiter._check_rate_limit(key, max_requests, window_seconds):
                    logger.warning(
                        f"Rate limit exceeded for {key} "
                        f"({max_requests} requests per {window_seconds}s)"
                    )
                    abort(429, description="Too many requests. Please try again later.")
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    @staticmethod
    def _check_rate_limit(key, max_requests, window_seconds):
        """
        Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        with rate_limit_lock:
            # Clean old requests
            rate_limit_storage[key] = [
                req_time for req_time in rate_limit_storage[key]
                if req_time > window_start
            ]
            
            # Check limit
            if len(rate_limit_storage[key]) >= max_requests:
                return False
            
            # Add current request
            rate_limit_storage[key].append(now)
            return True


def sanitize_input(value, allow_html=False):
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        value: Input value to sanitize
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized value
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        return value
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    if not allow_html:
        # Escape HTML characters
        value = (value
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;')
                .replace('/', '&#x2F;'))
    
    return value


def validate_objectid(value):
    """
    Validate MongoDB ObjectId string format.
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if valid ObjectId format
    """
    if not isinstance(value, str):
        return False
    
    if len(value) != 24:
        return False
    
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def secure_filename(filename):
    """
    Make a filename secure for file system storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Secure filename
    """
    import re
    import unicodedata
    
    # Normalize unicode
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Keep only alphanumeric, dots, dashes, underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}.{ext}" if ext else name


class SecurityConfig:
    """Security configuration validator."""
    
    @staticmethod
    def validate_config(app):
        """
        Validate security configuration.
        
        Args:
            app: Flask application instance
            
        Raises:
            ValueError: If configuration is insecure
        """
        errors = []
        warnings = []
        
        # Check SECRET_KEY
        secret_key = app.config.get('SECRET_KEY')
        if not secret_key or secret_key == 'dev' or len(secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        
        # Check JWT_SECRET_KEY
        jwt_key = app.config.get('JWT_SECRET_KEY')
        if not jwt_key or jwt_key == 'dev' or len(jwt_key) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters long")
        
        # Check session security
        if app.config.get('ENV') == 'production':
            if not app.config.get('SESSION_COOKIE_SECURE'):
                warnings.append("SESSION_COOKIE_SECURE should be True in production")
            
            if not app.config.get('SESSION_COOKIE_HTTPONLY'):
                errors.append("SESSION_COOKIE_HTTPONLY must be True")
            
            if app.config.get('DEBUG'):
                errors.append("DEBUG must be False in production")
        
        # Check MongoDB URI doesn't contain credentials in code
        mongodb_uri = app.config.get('MONGODB_URI', '')
        if '@' in mongodb_uri and 'localhost' not in mongodb_uri:
            # This is OK if it comes from environment variable
            if mongodb_uri == app.config.get('MONGODB_URI'):
                warnings.append("MongoDB credentials should only come from environment variables")
        
        # Log results
        if errors:
            error_msg = "Security configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if warnings:
            warning_msg = "Security configuration warnings:\n" + "\n".join(f"  - {w}" for w in warnings)
            logger.warning(warning_msg)
        
        logger.info("Security configuration validated successfully")


def require_https():
    """
    Decorator to enforce HTTPS on routes.
    
    Usage:
        @app.route('/secure-endpoint')
        @require_https()
        def secure_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_secure and current_app.config.get('ENV') == 'production':
                logger.warning(f"Non-HTTPS request to {request.path} from {request.remote_addr}")
                abort(403, description="HTTPS required")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
