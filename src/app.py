"""
Main Flask application factory.

This module creates and configures the Flask application with all
blueprints, middleware, and error handlers.
"""

from flask import Flask, render_template, session
from config.settings import get_config
from config.database import db
from utils.security import (
    SecurityHeaders, CSRFProtection, RateLimiter, SecurityConfig
)
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application factory function.

    Args:
        config_name (str, optional): Configuration environment name.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Validate security configuration
    SecurityConfig.validate_config(app)

    # Initialize security middleware
    SecurityHeaders.init_app(app)
    CSRFProtection.init_app(app)
    RateLimiter.init_app(app)

    # Initialize session storage (Redis for production, filesystem for dev)
    init_session_storage(app)

    # Initialize database with connection pooling
    db.initialize(
        app.config['MONGODB_URI'], 
        app.config['MONGODB_DB_NAME'],
        max_pool_size=app.config.get('MONGODB_MAX_POOL_SIZE', 100),
        min_pool_size=app.config.get('MONGODB_MIN_POOL_SIZE', 10),
        server_selection_timeout_ms=app.config.get('MONGODB_SERVER_SELECTION_TIMEOUT_MS', 5000),
        connect_timeout_ms=app.config.get('MONGODB_CONNECT_TIMEOUT_MS', 10000),
        socket_timeout_ms=app.config.get('MONGODB_SOCKET_TIMEOUT_MS', 20000)
    )

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register template filters
    register_template_filters(app)

    logger.info(f"Application created with config: {config_name or 'default'}")
    logger.info("Security features enabled: CSRF, Security Headers, Rate Limiting")

    return app


def init_session_storage(app):
    """
    Initialize session storage based on configuration.
    Uses Redis for production (horizontal scaling) or filesystem for development.

    Args:
        app (Flask): Flask application instance.
    """
    session_type = app.config.get('SESSION_TYPE', 'filesystem')
    
    if session_type == 'redis':
        try:
            import redis
            from flask_session import Session
            
            # Configure Redis connection
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            app.config['SESSION_REDIS'] = redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Initialize Flask-Session
            Session(app)
            logger.info(f"Redis session storage initialized: {redis_url}")
            
        except ImportError:
            logger.warning("redis or flask-session not installed. Falling back to filesystem sessions.")
            logger.warning("Install with: pip install redis flask-session")
            app.config['SESSION_TYPE'] = 'filesystem'
            init_filesystem_session(app)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Falling back to filesystem sessions")
            app.config['SESSION_TYPE'] = 'filesystem'
            init_filesystem_session(app)
    else:
        init_filesystem_session(app)


def init_filesystem_session(app):
    """
    Initialize filesystem-based session storage (for development only).
    
    Args:
        app (Flask): Flask application instance.
    """
    try:
        from flask_session import Session
        
        # Create session directory if it doesn't exist
        session_dir = app.config.get('SESSION_FILE_DIR', 
                                     os.path.join(os.path.dirname(__file__), '.flask_session'))
        os.makedirs(session_dir, exist_ok=True)
        
        Session(app)
        logger.info(f"Filesystem session storage initialized: {session_dir}")
        logger.warning("Using filesystem sessions - not recommended for production!")
        
    except ImportError:
        logger.warning("flask-session not installed. Using default Flask sessions (server memory).")
        logger.warning("Install with: pip install flask-session")
        logger.warning("NOTE: Default sessions do not support horizontal scaling!")


def register_blueprints(app):
    """
    Register all application blueprints.

    Args:
        app (Flask): Flask application instance.
    """
    # Import blueprints
    from modules.auth.routes import auth_bp
    from modules.dashboard.routes import dashboard_bp
    from modules.products.routes import products_bp
    from modules.warehouses.routes import warehouses_bp
    from modules.receipts.routes import receipts_bp
    from modules.deliveries.routes import deliveries_bp
    from modules.transfers.routes import transfers_bp
    from modules.adjustments.routes import adjustments_bp
    from modules.stock.routes import stock_bp
    from modules.settings.routes import settings_bp
    from modules.profile.routes import profile_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(warehouses_bp, url_prefix='/warehouses')
    app.register_blueprint(receipts_bp, url_prefix='/receipts')
    app.register_blueprint(deliveries_bp, url_prefix='/deliveries')
    app.register_blueprint(transfers_bp, url_prefix='/transfers')
    app.register_blueprint(adjustments_bp, url_prefix='/adjustments')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    # Root route
    @app.route('/')
    def index():
        """Redirect to dashboard or login."""
        if 'user_id' in session:
            return render_template('dashboard/index.html')
        return render_template('auth/login.html')

    logger.info("Blueprints registered")


def register_error_handlers(app):
    """
    Register error handlers.

    Args:
        app (Flask): Flask application instance.
    """
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        if app.config['DEBUG']:
            return render_template('errors/404.html'), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        return render_template('errors/403.html'), 403

    logger.info("Error handlers registered")


def register_template_filters(app):
    """
    Register custom Jinja2 template filters.

    Args:
        app (Flask): Flask application instance.
    """
    from datetime import datetime

    @app.template_filter('datetime_format')
    def datetime_format(value, format='%d %b %Y %H:%M'):
        """Format datetime for display."""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except:
                return value
        return value.strftime(format)

    @app.template_filter('date_format')
    def date_format(value, format='%d %b %Y'):
        """Format date for display."""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except:
                return value
        return value.strftime(format)

    @app.template_filter('number_format')
    def number_format(value, decimals=2):
        """Format number with decimals."""
        if value is None:
            return '0.00'
        return f"{float(value):,.{decimals}f}"

    @app.template_filter('status_badge')
    def status_badge(status):
        """Return Bootstrap badge class for status."""
        status_classes = {
            'draft': 'secondary',
            'waiting': 'info',
            'ready': 'warning',
            'done': 'success',
            'completed': 'success',
            'cancelled': 'danger',
            'pick': 'info',
            'pack': 'warning',
            'validate': 'primary',
            'shipped': 'success',
            'in_transit': 'warning',
            'approved': 'success'
        }
        return status_classes.get(status, 'secondary')

    logger.info("Template filters registered")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
