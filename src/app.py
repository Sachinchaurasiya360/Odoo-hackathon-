"""
Main Flask application factory.

This module creates and configures the Flask application with all
blueprints, middleware, and error handlers.
"""

from flask import Flask, render_template, session
from config.settings import get_config
from config.database import db
import logging

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

    # Initialize database
    db.initialize(app.config['MONGODB_URI'], app.config['MONGODB_DB_NAME'])

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register template filters
    register_template_filters(app)

    logger.info(f"Application created with config: {config_name or 'default'}")

    return app


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
