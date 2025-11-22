"""
Settings and configuration routes.

This module defines routes for system settings and configuration.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.decorators import login_required, role_required
from config.database import get_db
import logging

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
@role_required(['admin', 'manager'])
def index():
    """Settings main page."""
    return render_template('settings/index.html')

@settings_bp.route('/general', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def general():
    """General system settings."""
    try:
        db = get_db()
        
        if request.method == 'POST':
            # Update general settings
            settings_data = {
                'company_name': request.form.get('company_name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address'),
                'currency': request.form.get('currency', 'USD'),
                'timezone': request.form.get('timezone', 'UTC')
            }
            
            db.settings.update_one(
                {'type': 'general'},
                {'$set': settings_data},
                upsert=True
            )
            
            flash("General settings updated successfully", "success")
            return redirect(url_for('settings.general'))
        
        # GET request
        settings = db.settings.find_one({'type': 'general'}) or {}
        return render_template('settings/general.html', settings=settings)
        
    except Exception as e:
        logger.error(f"Error updating general settings: {e}")
        flash(f"Error updating settings: {str(e)}", "danger")
        return redirect(url_for('settings.index'))

@settings_bp.route('/warehouses')
@login_required
@role_required(['admin', 'manager'])
def warehouses():
    """Warehouse settings - redirects to warehouses module."""
    return redirect(url_for('warehouses.list_warehouses'))

@settings_bp.route('/users')
@login_required
@role_required(['admin'])
def users():
    """User management settings."""
    try:
        db = get_db()
        users = list(db.users.find({}, {'password': 0}))
        return render_template('settings/users.html', users=users)
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        flash(f"Error loading users: {str(e)}", "danger")
        return redirect(url_for('settings.index'))
