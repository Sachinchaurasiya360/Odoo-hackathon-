"""
Warehouse management routes.

This module defines routes for Warehouse management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from config.database import get_db
from models.warehouse import Warehouse
import logging

logger = logging.getLogger(__name__)

warehouses_bp = Blueprint('warehouses', __name__)

@warehouses_bp.route('/')
@login_required
def list_warehouses():
    """List all warehouses."""
    try:
        db = get_db()
        warehouses = list(db.warehouses.find())
        return render_template('warehouses/list.html', warehouses=warehouses)
    except Exception as e:
        logger.error(f"Error listing warehouses: {e}")
        flash("Error loading warehouses", "danger")
        return render_template('warehouses/list.html', warehouses=[])

@warehouses_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_warehouse():
    """Create a new warehouse."""
    if request.method == 'POST':
        try:
            db = get_db()
            code = request.form.get('code')
            name = request.form.get('name')
            location = request.form.get('location')
            is_active = request.form.get('is_active') == 'on'
            
            # Check if code exists
            if db.warehouses.find_one({'code': code}):
                flash(f"Warehouse with code {code} already exists", "danger")
                return render_template('warehouses/create.html')
            
            warehouse = Warehouse(
                code=code,
                name=name,
                location=location,
                is_active=is_active
            )
            
            db.warehouses.insert_one(warehouse.to_mongo())
            flash(f"Warehouse {name} created successfully", "success")
            return redirect(url_for('warehouses.list_warehouses'))
            
        except Exception as e:
            logger.error(f"Error creating warehouse: {e}")
            flash(f"Error creating warehouse: {str(e)}", "danger")
            
    return render_template('warehouses/create.html')

@warehouses_bp.route('/<warehouse_id>')
@login_required
def view_warehouse(warehouse_id):
    """View warehouse details."""
    # TODO: Implement view logic
    return render_template('warehouses/detail.html')

@warehouses_bp.route('/<warehouse_id>/edit', methods=['GET', 'POST'])
@login_required
def update_warehouse(warehouse_id):
    """Update warehouse."""
    # TODO: Implement update logic
    return render_template('warehouses/edit.html')
