"""
Delivery routes.

This module defines routes for managing outgoing inventory deliveries.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from modules.deliveries.service import DeliveryService
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from utils.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF
import logging

logger = logging.getLogger(__name__)

deliveries_bp = Blueprint('deliveries', __name__)
delivery_service = DeliveryService()


@deliveries_bp.route('/')
@login_required
def list_deliveries():
    """List all deliveries with filters."""
    page = request.args.get('page', 1, type=int)
    warehouse_id = request.args.get('warehouse_id')
    status = request.args.get('status')

    try:
        result = delivery_service.list_deliveries(
            warehouse_id=warehouse_id,
            status=status,
            page=page,
            per_page=20
        )
        
        status_counts = delivery_service.get_status_counts(warehouse_id)

        return render_template(
            'deliveries/list.html',
            deliveries=result['deliveries'],
            pagination=result,
            current_warehouse=warehouse_id,
            current_status=status,
            status_counts=status_counts
        )

    except Exception as e:
        logger.error(f"Error listing deliveries: {e}")
        flash('Error loading deliveries', 'danger')
        return render_template('deliveries/list.html', deliveries=[], pagination={})


@deliveries_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def create_delivery():
    """Create a new delivery."""
    if request.method == 'GET':
        return render_template('deliveries/create.html')

    # Handle POST request
    try:
        warehouse_id = request.form.get('warehouse_id')
        customer_name = request.form.get('customer_name')
        customer_address = request.form.get('customer_address', '')
        scheduled_date = request.form.get('scheduled_date')
        notes = request.form.get('notes', '')

        # Parse items from form
        items = []
        item_count = int(request.form.get('item_count', 0))
        
        for i in range(item_count):
            product_id = request.form.get(f'items[{i}][product_id]')
            ordered_quantity = request.form.get(f'items[{i}][ordered_quantity]')
            unit_price = request.form.get(f'items[{i}][unit_price]', 0)
            
            if product_id and ordered_quantity:
                items.append({
                    'product_id': product_id,
                    'ordered_quantity': float(ordered_quantity),
                    'unit_price': float(unit_price) if unit_price else 0
                })

        if not items:
            flash('At least one item is required', 'danger')
            return render_template('deliveries/create.html')

        delivery = delivery_service.create_delivery(
            warehouse_id=warehouse_id,
            customer_name=customer_name,
            customer_address=customer_address,
            items=items,
            scheduled_date=scheduled_date,
            notes=notes,
            created_by=session.get('user_id')
        )

        flash(f"Delivery {delivery['delivery_number']} created successfully", 'success')
        return redirect(url_for('deliveries.view_delivery', delivery_id=delivery['_id']))

    except Exception as e:
        logger.error(f"Error creating delivery: {e}")
        flash(f'Error creating delivery: {str(e)}', 'danger')
        return render_template('deliveries/create.html')


@deliveries_bp.route('/<delivery_id>')
@login_required
def view_delivery(delivery_id):
    """View delivery details."""
    try:
        delivery = delivery_service.get_delivery(delivery_id)
        
        if not delivery:
            flash('Delivery not found', 'danger')
            return redirect(url_for('deliveries.list_deliveries'))

        return render_template('deliveries/detail.html', delivery=delivery)

    except Exception as e:
        logger.error(f"Error viewing delivery: {e}")
        flash('Error loading delivery', 'danger')
        return redirect(url_for('deliveries.list_deliveries'))


@deliveries_bp.route('/<delivery_id>/transition', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def transition_delivery_status(delivery_id):
    """Transition delivery to new status."""
    try:
        new_status = request.form.get('status')
        
        if not new_status:
            flash('Status is required', 'danger')
            return redirect(url_for('deliveries.view_delivery', delivery_id=delivery_id))

        delivery = delivery_service.transition_status(
            delivery_id=delivery_id,
            new_status=new_status,
            changed_by=session.get('user_id')
        )

        flash(f"Delivery transitioned to {new_status}", 'success')
        return redirect(url_for('deliveries.view_delivery', delivery_id=delivery_id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('deliveries.view_delivery', delivery_id=delivery_id))
    except Exception as e:
        logger.error(f"Error transitioning delivery status: {e}")
        flash('Error updating delivery status', 'danger')
        return redirect(url_for('deliveries.view_delivery', delivery_id=delivery_id))


# API Endpoints
@deliveries_bp.route('/api/deliveries', methods=['GET'])
@login_required
def api_list_deliveries():
    """API endpoint to list deliveries."""
    try:
        page = request.args.get('page', 1, type=int)
        warehouse_id = request.args.get('warehouse_id')
        status = request.args.get('status')

        result = delivery_service.list_deliveries(
            warehouse_id=warehouse_id,
            status=status,
            page=page,
            per_page=20
        )

        return success_response(result)

    except Exception as e:
        logger.error(f"API error listing deliveries: {e}")
        return error_response(str(e))


@deliveries_bp.route('/api/deliveries/<delivery_id>', methods=['GET'])
@login_required
def api_get_delivery(delivery_id):
    """API endpoint to get delivery details."""
    try:
        delivery = delivery_service.get_delivery(delivery_id)
        
        if not delivery:
            return error_response('Delivery not found', status_code=404)

        return success_response(delivery)

    except Exception as e:
        logger.error(f"API error getting delivery: {e}")
        return error_response(str(e))
